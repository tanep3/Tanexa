# Tanexa

## 概要  
自作スマートスピーカー（音声チャットボット）システムです。  
ご自身のPCのローカル環境で稼働し、AIと会話を楽しむことができるアプリです。  
※Raspberry Pi OSとintel Macで動作確認をしています。

## インストール方法  
### 1. **voicevox_engineのインストール**  
[voicevox_engine](https://github.com/VOICEVOX/voicevox_engine)のユーザーガイドに従ってインストールして下さい。

### 2. **tane_chatのインストール**  
[tane_chat](https://github.com/tanep3/tane_chat)のインストール方法に従ってインストールして下さい。  
※Windowsの場合は、ボリュームマウントの表記に気をつけてください。以下は例です。  
```bash
volumes:
    - /C/Users/tane/llm/elyza-llama-3-jp-8b-Q4_K_M.gguf:/app/model
```

### 3. **VOSK言語モデルのダウンロード**  
[VOSKのサイト](https://alphacephei.com/vosk/models)から、音声認識のモデルファイルをダウンロードし、zipを解凍してから、任意の場所に配置して下さい。  
オススメは、[vosk-model-ja-0.22](https://alphacephei.com/vosk/models/vosk-model-ja-0.22.zip)です。
 
### 4. **Tanexaのインストール**  
(1)TanexaをGitでクローン（ダウンロード）します。
```bath
git clone https://github.com/tanep3/Tanexa.git
cd Tanexa
```
**config.yml**の必要な箇所をご自身の環境に合わせて修正して下さい。  
**vosk_model_path**には、上記 3. で配置したモデルファイルのフォルダパスを指定して下さい。  
(例)
```bash
# Mac、Linuxの場合
    "vosk_model_path": "/home/tane/datas/voice/vosk-model-ja-0.22",
# Windowsの場合
    "vosk_model_path": "/C/Users/tane/datas/vosk-model-ja-0.22",
```

(2)**Mac、ubuntu、RaspberryPiOSの場合**  
setup.shは初期セットアップ用のスクリプトです。start.shはTanexa起動用のスクリプトです。  
setup.sh、start.sh に実行権限を付けます。  
```bash
chmod +x setup.sh
chmod +x start.sh
```
最初に１回だけ**setup.sh**を実行します。  
Tanexaの起動は**start.sh**です。  
終了は**Ctrl+c**です。  

(3)**windowsの場合**  
- **Python 3.11.x**が必要です。[公式サイト](https://www.python.org/downloads/release/python-3112/)からダウンロードしてインストールしてください。  
- **Microsoft Visual C++ Build Tools**が必要です。[公式サイト](https://visualstudio.microsoft.com/ja/visual-cpp-build-tools/)からダウンロードしてインストールしてください。  
- Tanexaのセットアップ＆起動  
setup.batは初期セットアップ用のスクリプトです。start.batはTanexa起動用のスクリプトです。  
最初に１回だけ**setup.bat**を実行します。
```bash
.\setup.bat
```  
Tanexaの起動は**start.bat**です。  
```bash
.\start.bat
```  
終了は**Ctrl+c**です。  

### 4. **使い方**
当システムを動かしているPCにマイクとスピーカーを接続して下さい。  
ウェイクワードを認識すると「はい、なんでしょう？」と返答します。  
それを受けて、任意の質問を投げ返して下さい。なんらかの返答が帰ってきます。  
返答速度は、tane_chat、voicevox-engineを動かしているマシンスペックによります。  

## VOICEVOX ずんだもん 使用について
本システムでは、VOICEVOXの「ずんだもん」を使用しています。  
各キャラクターの音声の使用に関するガイドラインは、VOICEVOXの[各キャラクターの利用規約](https://voicevox.hiroshiba.jp)を参照してください。

## 著作者
- 著作者: **たねちゃんねる**

## ライセンス
このシステムはMITライセンスの下で公開されています。  
詳細は[LICENSE](./LICENSE)ファイルを参照してください。
