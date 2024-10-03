import yaml
import os

def get():
    # デフォルト値
    config_dict = {
        "wake_word": "コンピュータ",
        "mic_samplerate": 16000,
        "vosk_model_path": "/home/tane/vosk_model",
        "vosk_samplerate": 16000,
        "vosk_blocksize": 2048,
        "silence_duration": 3.5,
        "llm_URL": "http://127.0.0.1:5005",
        "llm_system_prompt": "あなたは日本人です。どんな簡単な単語でも、全て日本語で回答して下さい。５０文字以内に要約して回答してください。",
        "llm_max_tokens": 256,
        "voicevox_URL": "http://127.0.0.1:50021",
        "voicevox_speaker_id": 3,
        "voicevox_speedScale": 1.0,
        "voicevox_prePhonemeLength": 0.6,
        "voicevox_outputSamplingRate": 16000
    }

    # configファイルを読み込む
    filename = os.path.join(os.path.dirname(__file__), '..', 'config.yml')
    with open(filename, 'r', encoding='utf-8') as f:
        config_yml = yaml.safe_load(f)

    env_list = config_yml.get('environment', [])

    for item in env_list:
        # コメントを除去
        item_no_comment = item.split('#', 1)[0].strip()
        
        if '=' in item_no_comment:
            key, value = item_no_comment.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # 値を int または float に変換
            try:
                value_converted = int(value)
            except ValueError:
                try:
                    value_converted = float(value)
                except ValueError:
                    value_converted = value  # 数値に変換できない場合はそのまま文字列として保持
            
            config_dict[key] = value_converted

    return config_dict
