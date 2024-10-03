import numpy as np
from regex import W
import webrtcvad
import vosk
import json
import scipy.signal
from multiprocessing import Process, Queue, Event, Pipe
import pyaudio
import time
from abc import ABC, abstractmethod

# キューをこのイベントバスで管理する。
# パブリッシュ/サブスクライブ パターン
class EventBus:
    def __init__(self):
        self.queues = {}

    def subscribe(self, event_type, queue):
        # 指定されたイベントタイプに対するサブスクライバーを追加
        self.queues[event_type] = queue

    def publish(self, event_type, data):
        # 指定されたイベントタイプにメッセージを送信
        self.queues[event_type].put(data)
    
    def get_queue(self, event_type):
        return self.queues[event_type]

# 各processの共通の振る舞いを定義する抽象クラス。
# クラスは具体的な実装に依存するのではなく、抽象クラスやインターフェースに依存するべきという原則（依存性逆転の原則）
class RecognitionProcess(ABC):
    def __init__(self, event_bus, stop_event, in_event_type, out_event_type):
        self.event_bus = event_bus
        self.stop_event = stop_event
        self.in_event_type = in_event_type
        self.out_event_type = out_event_type

    @abstractmethod
    def run(self):
        pass

# 入力音声を16000Hzサンプリングに変換するプロセス
class ResampleAudioProcess(RecognitionProcess):
    def __init__(self, event_bus, stop_event, in_event_type, out_event_type, config):
        super().__init__(event_bus, stop_event, in_event_type, out_event_type)
        self.original_rate = config["mic_samplerate"]
        self.target_rate = config["vosk_samplerate"]

    def subscribe_Queue(self):
        self.event_bus.subscribe(self.out_event_type, Queue())

    def run(self):
        while not self.stop_event.is_set():
            audio_chunk = self.event_bus.get_queue(self.in_event_type).get()
            if audio_chunk is None:
                break
            resampled_audio = self.resample_audio_scipy(audio_chunk)
            self.event_bus.publish(self.out_event_type, resampled_audio)
        self.event_bus.publish(self.out_event_type, None)

    # 音声のリサンプリング処理
    def resample_audio_scipy(self, audio_data):
        if audio_data.ndim > 1:
            audio_data = audio_data[:, 0]  # 1チャネルに変換
        audio_data = audio_data.astype(np.float32)
        resampled_data = scipy.signal.resample_poly(audio_data, self.target_rate, self.original_rate)
        return resampled_data.astype(np.int16)

# 音声のノイズ除去、無音時間の計測を行うプロセス
class VadProcess(RecognitionProcess):
    def __init__(self, event_bus, stop_event, in_event_type, out_event_type, vad_child_conn, config):
        super().__init__(event_bus, stop_event, in_event_type, out_event_type)
        self.vad_child_conn = vad_child_conn
        self.config = config
        self.samplerate = config["vosk_samplerate"]

    def subscribe_Queue(self):
        self.event_bus.subscribe(self.out_event_type, Queue())

    def run(self, is_measure_silence_time):
        speech_detected = False
        silence_duration = self.config["silence_duration"] # 発話後の無音時間。これを経過したら聞き取りをやめる。
        silence_data = np.zeros(int(self.samplerate * 1.0), dtype=np.int16) # 有音の後、無音が来たらこれをくっつけ1秒間無音時間を長くする。
        buffer_audio = [silence_data]  # バッファに音声を蓄積
        max_silence_frames = self.samplerate * silence_duration
        silence_frames = 0

        while not self.stop_event.is_set():
            resampled_audio = self.event_bus.get_queue(self.in_event_type).get()
            if resampled_audio is None:
                break
            is_voice = self.is_speech_vad(resampled_audio)
            # VADで音声を検出した場合、バッファに追加
            if is_voice:
                speech_detected = True
                buffer_audio.append(resampled_audio)
            else:
                if speech_detected:
                    buffer_audio.append(resampled_audio)
                    buffer_audio.append(silence_data)     # 後に無音を追加
                    combined_audio = np.concatenate(buffer_audio)  # バッファ内の音声を結合
                    self.event_bus.publish(self.out_event_type, combined_audio)  # VOSKプロセスに音声を送信
                    buffer_audio = [silence_data]  # バッファをクリア
                    speech_detected = False
                    silence_frames = 0
                else:
                    if is_measure_silence_time:
                        # VADで音声を検出しなかった場合、無音時間を計測し、指定時間経過したら処理を終了する。
                        silence_frames += len(np.frombuffer(resampled_audio, dtype=np.int16))
                        if silence_frames >= max_silence_frames:
                            print(f"{silence_duration}秒経過しました。")
                            break
        self.event_bus.publish(self.out_event_type, None)

    # VADにより、そのチャンクが有音かどうかを調べる関数
    def is_speech_vad(self, audio_chunk):
        frame_size = int(self.samplerate * 0.03)  # フレームサイズを30msに設定
        vad_audio_chunk = np.frombuffer(audio_chunk, dtype=np.int16)
        # 音声データ全体をフレームごとに評価する
        for i in range(0, len(vad_audio_chunk), frame_size):
            frame = vad_audio_chunk[i:i + frame_size]  # フレームを取り出す
            if len(frame) < frame_size:
                break  # フレームが不足している場合は評価せずに終了
            self.vad_child_conn.send((frame.tobytes(), self.samplerate))
            result = self.vad_child_conn.recv()
            if result:
                return True
        return False

# 音声認識を行うプロセス
class VoskProcess(RecognitionProcess):
    def __init__(self, event_bus, stop_event, in_event_type, out_event_type, vosk_child_conn, config):
        super().__init__(event_bus, stop_event, in_event_type, out_event_type)
        self.vosk_child_conn = vosk_child_conn
        self.config = config

    def subscribe_Queue(self):
        self.event_bus.subscribe(self.out_event_type, Queue())

    def run(self):
        vosk_buffer = []
        VOSK_BUFFER_MIN = int(0.5 * self.config["vosk_samplerate"]) # 0.5秒×16000Hz
        while not self.stop_event.is_set():
            resampled_audio = self.event_bus.get_queue(self.in_event_type).get()
            if resampled_audio is None:
                break
            vosk_buffer.append(resampled_audio)
            combined_audio = np.concatenate(vosk_buffer)
            if len(combined_audio) < VOSK_BUFFER_MIN:
                continue
            vosk_buffer = []
            recognized_text = self.vosk_recognize_audio(combined_audio)  # VOSKで認識
            self.event_bus.publish(self.out_event_type, recognized_text)
            print(f"Recognized: {recognized_text}")
        self.event_bus.publish(self.out_event_type, None)

    # VOSKによる音声認識処理
    def vosk_recognize_audio(self, audio_buffer):
        """
        VOSKを使って音声チャンクの認識を行う
        """
        audio_bytes = audio_buffer.tobytes()
        # 音声データをVOSKに渡して認識
        self.vosk_child_conn.send(audio_bytes)
        recoginizer_result = self.vosk_child_conn.recv()
        return recoginizer_result

# ウェイクワード判定プロセス
class WakeWordProcess(RecognitionProcess):
    def __init__(self, event_bus, stop_event, in_event_type, out_event_type, config):
        super().__init__(event_bus, stop_event, in_event_type, out_event_type)
        self.wake_word = config["wake_word"]

    def run(self):
        while not self.stop_event.is_set():
            recognized_text = self.event_bus.get_queue(self.in_event_type).get()
            if recognized_text is None:
                break
            if self.wake_word in recognized_text:
                print(f"ウェイクワード '{self.wake_word}' 検出！")
                break

# 認識された文字列を蓄積するプロセス
class TextAccumulationProcess(RecognitionProcess):
    def __init__(self, event_bus, stop_event, in_event_type, out_event_type):
        super().__init__(event_bus, stop_event, in_event_type, out_event_type)

    def run(self):
        while not self.stop_event.is_set():
            time.sleep(0.05)
            continue

# プロセスを統合管理するクラス
class ProcessManagement():
    def __init__(self, vad_child_conn, vosk_child_conn, config):
        self.config = config
        self.event_bus = EventBus()
        self.stop_event = Event()  # プロセス停止用のイベントフラグ
        self.resample_audio_process_instance = ResampleAudioProcess(self.event_bus, self.stop_event, "mic_audio", "resampled_audio", self.config)
        self.vad_process_instance = VadProcess(self.event_bus, self.stop_event, "resampled_audio", "vad_audio", vad_child_conn, self.config)
        self.vosk_process_instance = VoskProcess(self.event_bus, self.stop_event, "vad_audio", "recognized_text", vosk_child_conn, self.config)
        self.recognized_word_process_instance = None

    # マイクからの音声データ取得
    def audio_callback(self, indata, frames, time_info, status, in_event_type):
        if status:
            print(status)
        if indata:
            audio_data = np.frombuffer(indata, dtype=np.int16)
            self.event_bus.publish(in_event_type, audio_data)  # 音声データをキューに追加
        return (None, pyaudio.paContinue)

    def start_process(self, is_measure_silence_time):
        # EventBusの初期化
        self.event_bus.subscribe("mic_audio", Queue())
        self.resample_audio_process_instance.subscribe_Queue()
        self.vad_process_instance.subscribe_Queue()
        self.vosk_process_instance.subscribe_Queue()
        # ストリームをループ実行できるようにする。
        running = True
        # プロセス停止用のEventフラグをOFFにする。
        self.stop_event.clear()
        # 並列プロセスを作成
        resample_audio_process = Process(target=self.resample_audio_process_instance.run, args=())
        vad_process = Process(target=self.vad_process_instance.run, args=(is_measure_silence_time,))
        vosk_process = Process(target=self.vosk_process_instance.run, args=())
        recognized_word_process = Process(target=self.recognized_word_process_instance.run, args=())
        # マイクから音声入力を取得し、音声データをキューに送信
        p = pyaudio.PyAudio()
        default_device_index = p.get_default_input_device_info()['index']
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=self.config["mic_samplerate"],
                        input=True,
                        input_device_index=default_device_index,
                        frames_per_buffer=self.config["vosk_blocksize"],
                        stream_callback=lambda indata, frames, time_info, status:
                            self.audio_callback(indata, frames, time_info, status, "mic_audio"))
        # ストリームの開始
        stream.start_stream()
        # プロセスの開始
        resample_audio_process.start()
        vad_process.start()
        vosk_process.start()
        recognized_word_process.start()
        # 無限ループだが、runningがFalseになると停止
        while running:
            time.sleep(0.01)
            # 一つでもプロセスが終了したら、全てのプロセスを止めて終了する。
            if not resample_audio_process.is_alive() or \
               not vad_process.is_alive() or \
               not vosk_process.is_alive() or \
               not recognized_word_process.is_alive():
                # ストリームを停止
                running = False  # ループを抜けるためにフラグをFalseにする
                # フラグをセットしてプロセスに終了シグナルを送る
                self.event_bus.publish("mic_audio", None)
                self.stop_event.set()
        # if stream is not None:
        stream.stop_stream()
        stream.close()
        p.terminate()  # PyAudioの終了処理
        # プロセスの停止（フラグにより自動で終了するため、待機）
        if resample_audio_process.is_alive:
            resample_audio_process.join()  # 完全終了を待つ
        if vad_process.is_alive():
            vad_process.join()
        if vosk_process.is_alive():
            vosk_process.join()
        if recognized_word_process.is_alive():
            recognized_word_process.join()

    def set_wake_word_process(self):
        self.recognized_word_process_instance = WakeWordProcess(self.event_bus, self.stop_event, "recognized_text",None ,self.config)

    def set_text_accumulation_process(self):
        self.recognized_word_process_instance = TextAccumulationProcess(self.event_bus, self.stop_event, None, None)

    def get_recognized_word_queue(self):
        return self.event_bus.get_queue("recognized_text")

def detect_wake_word():
    process_manager.set_wake_word_process()
    is_measure_silence_time = False
    process_manager.start_process(is_measure_silence_time)

def record_and_transcribe():
    process_manager.set_text_accumulation_process()
    is_measure_silence_time = True
    process_manager.start_process(is_measure_silence_time)
    result_text = ''
    recognized_word_queue = process_manager.get_recognized_word_queue()
    while not recognized_word_queue.empty():
        try:
            recognized_text = recognized_word_queue.get_nowait()
            if recognized_text is not None:
                result_text += recognized_text
        except multiprocessing.queues.Empty:
            break
    return result_text

def vad_parent(conn, is_ready):
    # vadの初期化、設定
    vad = webrtcvad.Vad()
    vad.set_mode(2)  # 感度の設定
    is_ready.set()
    while True:
        try:
            frame, samplerate = conn.recv()
            result = vad.is_speech(frame, samplerate)
            conn.send(result)
        except BrokenPipeError:
            break

def vosk_parent(conn, config, is_ready):
    # voskの初期化、設定
    model = vosk.Model(config["vosk_model_path"])  # VOSKのモデルパス
    recognizer = vosk.KaldiRecognizer(model, config["vosk_samplerate"])
    is_ready.set()
    while True:
        try:
            audio_bytes = conn.recv()
            if recognizer.AcceptWaveform(audio_bytes):
                print('VOSK: OK')
                result = recognizer.Result()
                result_json = json.loads(result)
                conn.send(result_json.get('text'))
            else:
                print('VOSK: partial')
                final_result = recognizer.FinalResult()
                final_json = json.loads(final_result)
                conn.send(final_json.get('text'))
        except BrokenPipeError:
            break

def init(config):
    # グローバル処理
    global process_manager
    vad_parent_conn, vad_child_conn = Pipe()
    vosk_parent_conn, vosk_child_conn = Pipe()

    # 親プロセスの開始
    is_ready = Event()
    is_ready.clear()
    vad = Process(target=vad_parent, args=(vad_parent_conn,is_ready))
    vad.start()
    while not is_ready.is_set():
        continue
    vosk = Process(target=vosk_parent, args=(vosk_parent_conn,config, is_ready))
    vosk.start()
    is_ready.clear()
    while not is_ready.is_set():
        continue

    # プロセスマネージャーのインスタンス化
    process_manager = ProcessManagement(vad_child_conn, vosk_child_conn, config)

