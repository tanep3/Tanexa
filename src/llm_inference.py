import requests
import re
import speak
from multiprocessing import Process, Queue
import threading
import json

def generate_response_stream(user_input, config):
    """
    LLMモデルを使用して応答を逐次生成し、キューに格納する関数
    """
    llm_url = config["llm_URL"]
    llm_query_url = f"{llm_url}/generate"
    # prompt = f"###質問：{user_input}。###回答："
    prompt = re.sub(r'(/s)', "", user_input)
    prompt_json = json.dumps({
            "system_prompt": config["llm_system_prompt"],
            "user_input": prompt,
            "max_tokens": config["llm_max_tokens"],
            "stream": True
        })
    headers = {"Content-Type": "application/json"}

    sentence = ""
    try:
        response = requests.post(llm_query_url, headers=headers, data=prompt_json, stream=True)
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            buffer = chunk
            # 句読点、改行、記号が出てきたら、センテンス終了と判断する
            if re.search(r'(。|、|「|」|\.|！|!|？|\?|,|:|\s)$', buffer):
                # 句読点、改行、記号は削除する
                buffer = re.sub(r'(。|、|「|」|\.|！|!|？|\?|,|:|\s)', "", buffer)
                sentence += buffer
                if sentence:
                    output_sentence = sentence
                    sentence = ''
                    yield output_sentence
            else:
                sentence += buffer
    except Exception as e:
        print(f"応答生成中にエラーが発生しました: {e}")
    finally:
        if sentence:
            yield sentence  # 残りのテキストを出力

def process_with_llm(text, config):
    """
    非同期でLLMモデルによる推論を行う関数
    合成音声処理はプロセスで並列処理を行うが、音声再生は別プロセスだとデバイス競合がおき、
    再生エラーが起きるので、スレッドで並列処理を行う。
    """
    sentence_queue = Queue()
    voice_queue = Queue()

    # 合成音声処理を並行稼働させるため、音声合成ワーカープロセスを起動
    make_worker_process = Process(target=make_voice_worker, args=(sentence_queue, voice_queue, config))
    make_worker_process.start()

    # 音声再生スレッドを起動
    play_worker_thread = threading.Thread(target=play_voice_worker, args=(voice_queue,))
    play_worker_thread.start()

    # LLMにより１センテンスづつ回答を取得する。
    for sentence in generate_response_stream(text, config):
        print(sentence)
        sentence_queue.put(sentence)

    # 全ての文章をキューに追加したら、終了シグナルとして None を追加
    sentence_queue.put(None)

    # make_worker_process の終了を待機
    make_worker_process.join()

    # voice_queue に終了シグナルを追加
    voice_queue.put(None)

    # play_worker_thread の終了を待機
    play_worker_thread.join()


def make_voice_worker(sentence_queue, voice_queue, config):
    """
    音声合成ワーカープロセス
    """
    while True:
        text = sentence_queue.get()
        if text is None:
            break
        print("make_voice")
        # プロセスで実行
        # 音声データを生成
        voice_data = speak.make_voice(text, config)
        if voice_data:
            # 音声データをキューに追加
            voice_queue.put(voice_data)

def play_voice_worker(voice_queue):
    """
    音声再生スレッド
    """
    while True:
        voice = voice_queue.get()
        if voice is None:
            break
        print("play_voice")
        speak.play_voice(voice)