import requests
import io
import simpleaudio as sa
import wave

def make_voice(text, config):
    """
    テキストを音声合成して再生する関数
    """
    voicevox_url = config["voicevox_URL"]
    voicevox_speaker_id = config["voicevox_speaker_id"]
    # audio_query のリクエストを送信
    audio_query_url = f"{voicevox_url}/audio_query"
    audio_query_params = {"text": text, "speaker": voicevox_speaker_id}

    try:
        response = requests.post(audio_query_url, params=audio_query_params)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"audio_queryのリクエストに失敗しました: {e}")
        return None

    query_json = response.json()
    # 音声合成パラメータの調整
    query_json["speedScale"] = config["voicevox_speedScale"]
    query_json["prePhonemeLength"] = config["voicevox_prePhonemeLength"]
    query_json["outputSamplingRate"] = config["voicevox_outputSamplingRate"]

    # synthesis のリクエストを送信
    synthesis_url = f"{voicevox_url}/synthesis?speaker={voicevox_speaker_id}"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(synthesis_url, headers=headers, json=query_json)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"synthesisのリクエストに失敗しました: {e}")
        return None
    
    return response.content


def play_voice(voice):
    """
    生成された音声データを再生する関数
    """
    try:
        # `io.BytesIO`を使ってバイナリデータをWAVとして読み込む
        with io.BytesIO(voice) as wav_io:
            # waveモジュールを使ってWAVファイルとして扱う
            with wave.open(wav_io, 'rb') as wav_file:
                # simpleaudioで再生できる形式に変換
                wave_obj = sa.WaveObject.from_wave_read(wav_file)
                # 再生
                play_obj = wave_obj.play()
                # 再生が終了するまで待機
                play_obj.wait_done()
    except Exception as e:
        print(f"音声データの再生中にエラーが発生しました: {e}")
        print(f"エラーの詳細: {type(e).__name__}, {e.args}")

def play_system_sound(wav_file):
    """
    システムの音声ファイルを再生する関数
    """
    # 音声ファイルを読み込んで再生
    try:
        # WAVファイルの読み込み
        wave_obj = sa.WaveObject.from_wave_file(wav_file)
        # 再生
        play_obj = wave_obj.play()
        # # 再生が終了するまで待機
        # play_obj.wait_done()
    except Exception as e:
        print(f"音声再生中にエラーが発生しました: {e}")
