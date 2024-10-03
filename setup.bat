@echo off
chcp 65001 >NUL

REM Python 3.11.2のインストール確認
python --version 2>NUL | findstr /C:"Python 3.11" >NUL
IF %ERRORLEVEL% NEQ 0 (
    echo Python 3.11.xが見つかりません。公式サイトからインストールしてください。
    echo https://www.python.org/downloads/release/python-3112/
    pause
    exit /B 1
)

REM 必要なシステムライブラリのインストール案内
echo Microsoft Visual C++ Build Toolsが必要です。以下のサイトからダウンロードしてインストールしてください。
echo https://visualstudio.microsoft.com/ja/visual-cpp-build-tools/
pause

REM 仮想環境の作成
python -m venv venv

REM 仮想環境の有効化
call venv\Scripts\activate

REM pipのアップグレード
python -m pip install --upgrade pip

REM 依存関係のインストール
pip install pipwin
FOR /F "tokens=*" %%i IN (requirements.txt) DO (
    pip install %%i
    IF %ERRORLEVEL% NEQ 0 (
        pipwin install %%i
        IF %ERRORLEVEL% NEQ 0 (
            echo %%iのインストールに失敗しました。
            exit /b 1
        )
    )
)

echo セットアップが完了しました。'start.bat' でアプリケーションを起動できます。
pause
