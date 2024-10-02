# Python 3.11 ベースのランタイムイメージ
FROM python:3.11.2-slim AS runtime

# 作業ディレクトリを設定
WORKDIR /app

# 必要な依存パッケージをインストール
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y cmake make build-essential libopenblas-dev git pkg-config \
    libgomp1 libasound2-dev portaudio19-dev ffmpeg  \
    libwebrtc-audio-processing-dev libatlas-base-dev \
    gfortran pulseaudio pulseaudio-utils alsa-utils && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をインストール
COPY requirements.txt .
RUN CMAKE_ARGS="-DGGML_OPENMP=ON -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS -DCMAKE_EXE_LINKER_FLAGS='-lpthread -Wl,--no-as-needed -pthread'" pip install --no-cache-dir -r requirements.txt

# llama-cpp-python のインストールディレクトリに libllama.so が存在するので、LD_LIBRARY_PATH を設定
# 未定義の際は LD_LIBRARY_PATH のデフォルト値を空にする
RUN export LD_LIBRARY_PATH=/usr/local/lib/python3.11/site-packages/lib64:${LD_LIBRARY_PATH:-}
# 永続的に環境変数を設定するために ENV を使用する
ENV LD_LIBRARY_PATH="/usr/lib:${LD_LIBRARY_PATH}"

# アプリケーションのソースコードをコピー
COPY . .

# 非rootユーザーを作成
RUN useradd -m pulseuser

# PulseAudioの設定ディレクトリを作成
RUN mkdir -p /home/pulseuser/.config/pulse

# PulseAudioの設定ファイルを作成
RUN echo -e "autospawn = yes\ndaemon-binary = /usr/bin/pulseaudio" > /home/pulseuser/.config/pulse/client.conf

# ユーザーを切り替え
USER pulseuser


# エントリーポイントを設定
CMD ["python", "src/main.py"]