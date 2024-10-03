#!/bin/bash

# Pythonのバージョン
PYTHON_VERSION="3.11.2"

# システム依存ライブラリのインストール
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOSの場合
    echo "macOS用の依存関係をインストールしています..."

    # Homebrewがインストールされているか確認
    if ! command -v brew &> /dev/null; then
        echo -n "Homebrewが見つかりません。インストールしますか？(y/n): "
        read answer
        if [ "$answer" == "y" ] || [ "$answer" == "Y" ]; then
            echo "Homebrewをインストールしています..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        else
            echo "Homebrewが必要です。スクリプトを終了します。"
            exit 1
        fi
    fi

    # pyenvのインストール確認
    if ! command -v pyenv &> /dev/null; then
        echo "pyenvをHomebrewでインストールしています..."
        brew update
        brew install pyenv
    fi

    # シェルの設定ファイルにpyenvの初期化を追加
    SHELL_NAME=$(basename "$SHELL")
    if [ "$SHELL_NAME" == "bash" ]; then
        PROFILE_FILE="$HOME/.bash_profile"
    elif [ "$SHELL_NAME" == "zsh" ]; then
        PROFILE_FILE="$HOME/.zshrc"
    else
        PROFILE_FILE="$HOME/.profile"
    fi

    if ! grep -q 'pyenv init' "$PROFILE_FILE"; then
        echo 'export PYENV_ROOT="$HOME/.pyenv"' >> "$PROFILE_FILE"
        echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> "$PROFILE_FILE"
        echo -e 'eval "$(pyenv init -)"' >> "$PROFILE_FILE"
        source "$PROFILE_FILE"
    fi

    # 必要なライブラリのインストール
    brew install portaudio

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linuxの場合
    echo "Linux用の依存関係をインストールしています..."
    sudo apt-get update
    sudo apt-get install -y build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev \
    libportaudio2 libasound-dev libsndfile1 portaudio19-dev

    # pyenvのインストール確認
    if ! command -v pyenv &> /dev/null; then
        echo "pyenvをインストールしています..."
        sudo apt-get install -y make libssl-dev zlib1g-dev libbz2-dev \
        libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev \
        libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev

        curl https://pyenv.run | bash

        # シェルの設定ファイルにpyenvの初期化を追加
        SHELL_NAME=$(basename "$SHELL")
        if [ "$SHELL_NAME" == "bash" ]; then
            PROFILE_FILE="$HOME/.bashrc"
        elif [ "$SHELL_NAME" == "zsh" ]; then
            PROFILE_FILE="$HOME/.zshrc"
        else
            PROFILE_FILE="$HOME/.profile"
        fi

        if ! grep -q 'pyenv init' "$PROFILE_FILE"; then
            echo 'export PYENV_ROOT="$HOME/.pyenv"' >> "$PROFILE_FILE"
            echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> "$PROFILE_FILE"
            echo -e 'eval "$(pyenv init -)"' >> "$PROFILE_FILE"
            source "$PROFILE_FILE"
        fi
    fi

    # pyenvの初期化
    if command -v pyenv &> /dev/null; then
        eval "$(pyenv init -)"
    fi

else
    echo "サポートされていないOSです。手動で依存関係をインストールしてください。"
    exit 1
fi

# ターミナルの再読み込み
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Python 3.11.2のインストール確認
if ! pyenv versions | grep $PYTHON_VERSION > /dev/null; then
    echo "Python $PYTHON_VERSION が見つかりません。インストールします..."
    pyenv install $PYTHON_VERSION
fi

# Pythonバージョンをローカルに設定
pyenv local $PYTHON_VERSION

# 仮想環境の作成
echo "仮想環境を作成しています..."
python -m venv venv

# 仮想環境の有効化
echo "仮想環境を有効化しています..."
source venv/bin/activate

# pipのアップグレード
echo "pipをアップグレードしています..."
pip install --upgrade pip

# 依存関係のインストール
echo "依存関係をインストールしています..."
pip install -r requirements.txt

deactivate

echo "セットアップが完了しました。'start.sh' でアプリケーションを起動できます。"