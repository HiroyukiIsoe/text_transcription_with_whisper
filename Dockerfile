# Python 3.11.5のイメージをベースにする
FROM python:3.11.5

# 作業ディレクトリを設定
WORKDIR /app

# ホストのカレントディレクトリの内容をコンテナの作業ディレクトリにコピー
COPY . /app

# 必要なパッケージのインストール（例: もし必要であれば）
# RUN pip install -r requirements.txt

# アプリケーションを実行
# CMD ["python", "your_script.py"]  # "your_script.py"を実際のスクリプトのファイル名に置き換えてください
