# Tanexa

## 概要
自作スマートスピーカーシステムです。  
ご自身のPCのローカル環境で稼働し、AIと会話を楽しむことができるアプリです。  
- Raspberry Pi OSとintel Macで動作確認をしています。

## インストール方法
### 1. **voicevox_engineのインストール**
[voicevox_engine](https://github.com/VOICEVOX/voicevox_engine)のユーザーガイドに従ってインストールして下さい。

### 2. **tane_chatのインストール**
[tane_chat](https://github.com/tanep3/tane_chat)のインストール方法に従ってインストールして下さい。

### 3. **VOSK言語モデルのダウンロード**
[VOSKのサイト](https://alphacephei.com/vosk/models)から、音声認識のモデルファイルをダウンロードし、zipを解凍してから、任意の場所に配置して下さい。  
オススメは、[vosk-model-ja-0.22](https://alphacephei.com/vosk/models/vosk-model-ja-0.22.zip)です。

### 4. **Macの場合、PortAudioのインストール**
- Homebrewを使ってPortAudioをインストールします。  
```bash
brew install portaudio
```
 
### 5. **Tanexaのインストール**
(1)[docker-compose.yml](./docker-compose.yml)をダウンロードし、任意の場所に配置する。  
(2)docker-compose.ymlの必要な箇所をご自身の環境に合わせて修正して下さい。  
「/VOSKのモデルファイルを置いているパス」には、上記 3. で配置したモデルファイルのフォルダパスを指定して下さい。  
(例)   
```bash
    volumes:
      - /home/tane/vosk_model/vosk-model-ja-0.22:/app/vosk_model  # モデルファイルをコンテナにマウント
```
(3)Dockerにてインストールします。
```bash
docker-compose up -d
```

### 5. **使い方**
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
