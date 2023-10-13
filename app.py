import streamlit as st
import openai
import os
from typing import Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from datetime import datetime
import requests as req
import csv
from io import StringIO


class JapaneseCharacterTextSplitter(RecursiveCharacterTextSplitter):
    def __init__(self, **kwargs: Any):
        separators = ["\n\n", "\n", "。", "、", " ", ""]
        super().__init__(separators=separators, **kwargs)


japanese_spliter = JapaneseCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=0,
)

HATENA_ID = os.environ['HATENA_ID']
API_KEY = os.environ['HATENA_API_KEY']
BASE_URL = os.environ['HATENA_END_POINT']


def generate_title(content):
    prompt = f"##文章を要約し、短く簡潔なブログのタイトルを作成してください。\n文字数は20文字以下としてください。\n{content}\n"
    messages = [{"role": "system", "content": "あなたはブログのエディターです。"},
                {"role": "user", "content": prompt}
                ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0,
    )
    return response["choices"][0]["message"]["content"]


def generate_categories(content):
    prompt = f"##文章を要約しはてなブログに設定するカテゴリを5つ作成してください。\nカテゴリのみをCSVで表示してください。\n{content}\n"
    messages = [{"role": "system", "content": "あなたはブログのエディターです。\n"},
                {"role": "user", "content": prompt}
                ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0,
    )
    csv_data = list(csv.reader(
        StringIO(response["choices"][0]["message"]["content"])))

    return csv_data[0]


def hatena_entry(title, content, categorys=[], updated="", draft=False):
    updated = updated if updated else datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    draft = "yes" if draft else "no"
    def category(x): return "\n".join([f"<category term='{e}' />" for e in x])
    categorys = category(categorys) if category else ""

    xml = f"""<?xml version="1.0" encoding="utf-8"?><entry xmlns="http://www.w3.org/2005/Atom" xmlns:app="http://www.w3.org/2007/app">
      <title>{title}</title><author><name>name</name></author><content type="text/markdown">{content}</content>
      <updated>{updated}</updated>{categorys}<app:control><app:draft>{draft}</app:draft>
      </app:control></entry>""".encode(
        "UTF-8"
    )
    r = req.post(BASE_URL + "/entry", auth=(HATENA_ID, API_KEY), data=xml)
    return r.text


open_api_key = os.environ['OPENAI_API_KEY']
openai.api_key = open_api_key
st.title("ブログ自動投稿")
# 音声ファイルをアップロードする
audio_file = st.file_uploader(
    "音声ファイルをアップロードしてください", type=["mp3", "wav", "mp4"])
submit_btn = st.button("送信")
if submit_btn:
    st.write("音声ファイルを送信しました")
    trans_text = openai.Audio.transcribe("whisper-1", audio_file)["text"]
    st.success("文字起こしが完了しました")
    st.write(trans_text)
    st.write("日本語の修正とマークダウン形式への変換を開始します")
    texts = japanese_spliter.split_text(trans_text)
    texts_modified = ""
    for text in texts:
        prompt = f"##自然な文章に修正し、マークダウン形式で表示してください。また、適切なタイトルを設定してください。\n{text}\n"
        messages = [{"role": "system", "content": "あなたは優秀な日本語のエディターです。"},
                    {"role": "user", "content": prompt}
                    ]
        text_modified = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0,
        )
        texts_modified = texts_modified + \
            text_modified["choices"][0]["message"]["content"]

    title = generate_title(text_modified)

    st.write(f"""Title:{title}""")

    categories = generate_categories(texts_modified)

    st.write(categories)

    st.markdown(texts_modified)

    r = hatena_entry(title, texts_modified,
                     categorys=categories, updated="", draft=True)

    st.text_area("blog_entry", r)
