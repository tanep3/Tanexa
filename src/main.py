import os
import json
import time
import voice_recognition
import llm_inference
import speak

config = {
    "wake_word": os.getenv("TANEXA_WAKE_WORD", "コンピュータ"),
    "mic_samplerate": int(os.getenv("TANEXA_MIC_SAMPLE_RATE", 16000)),
    "vosk_model_path": os.getenv("TANEXA_VOSK_MODEL_PATH", "/app/vosk_model"),
    "vosk_samplerate": int(os.getenv("TANEXA_VOSK_SAMPLE_RATE", 16000)),
    "vosk_blocksize": int(os.getenv("TANEXA_VOSK_BLOCKSIZE", 2048)),
    "silence_duration": float(os.getenv("TANEXA_SILENCE_DURATION", 3.5)),
    "llm_URL": os.getenv("TANEXA_LLM_URL", "http://127.0.0.1:5005"),
    "llm_system_prompt": os.getenv("TANEXA_LLM_SYSTEM_PROMPT", "あなたは日本人です。どんな簡単な単語でも、全て日本語で回答して下さい。５０文字以内に要約して回答してください。"),
    "llm_max_tokens": int(os.getenv("TANEXA_LLM_MAX_TOKENS", 256)),
    "voicevox_URL": os.getenv("TANEXA_VOICEVOX_URL", "http://127.0.0.1:50021"),
    "voicevox_speaker_id": int(os.getenv("TANEXA_VOICEVOX_SPEAKER_ID", 3)),
    "voicevox_speedScale": float(os.getenv("TANEXA_VOICEVOX_SPEED_SCALE", 1.0)),
    "voicevox_prePhonemeLength": float(os.getenv("TANEXA_VOICEVOX_PREPHONEME_LENGTH", 0.6)),
    "voicevox_outputSamplingRate": int(os.getenv("TANEXA_VOICEVOX_OUTPUT_SAMPLING_RATE", 16000))
}

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
