import os
import json
import time
import voice_recognition
import llm_inference
import speak
import set_config

config = set_config.get("../config.yml")

if __name__ == "__main__":
    # llm_inference.llm_model_load(config)
    voice_recognition.init(config)
    speak.play_system_sound("./wav/kidoushimashita.wav")
    while True:
        print("ウェイクワードを待機中...")
        voice_recognition.detect_wake_word()  # ウェイクワードを呼ばれるまで、ここで処理がストップする。
        speak.play_system_sound("./wav/hainandesyou.wav")
        # time.sleep(0.5)
        text = voice_recognition.record_and_transcribe()
        if text:
            speak.play_system_sound("./wav/kangaemasu.wav")
            print("LLMに送信中...")
            llm_inference.process_with_llm(text, config)
            # 応答終了時の音声を再生
            speak.play_system_sound("./wav/ijoudesu.wav")
        else:
            speak.play_system_sound("./wav/kikoemasen.wav")
