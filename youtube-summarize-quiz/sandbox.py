import marimo

__generated_with = "0.17.7"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # import
    """)
    return


@app.cell
def _():
    from pathlib import Path
    import yt_dlp
    import re
    import json
    from dotenv import load_dotenv
    from google import genai
    import os
    return Path, genai, json, load_dotenv, os, re, yt_dlp


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 関数定義
    """)
    return


@app.cell
def _(genai):
    # LLMによる生成
    def LLM_gen(contents: str) -> str:
        client = genai.Client()

        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents= contents
        )
        return response.text
    # 危険な文字の除去
    def replace_chars(s: str) -> str:
        remove_chars = '\\/:*?"<>|￥＜＞｜'  # 削除対象文字
        table = str.maketrans({ch: '-' for ch in remove_chars})
        s2 = s.translate(table)
        s3 = s2.replace(" ","")
        return s3
    # srtファイルを削除したときにjsonファイルのdoneを全てfalseに修正
    return LLM_gen, replace_chars


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # youtubeの読み込み
    """)
    return


@app.cell
def _(Path, json, yt_dlp):
    # jsonファイルの読み込み
    youtube_links_file_name = 'youtube_links.json'
    youtube_links_path = Path(youtube_links_file_name)
    # if not youtube_links_path.exists():
    #     raise 
    _json_text = youtube_links_path.read_text(encoding='utf-8')
    _data = json.loads(_json_text)
    ydl_opts = {'skip_download': True, 'writesubtitles': True, 'writeautomaticsub': True, 'subtitleslangs': ['ja'], 'subtitlesformat': 'srt', 'outtmpl': 'captions/%(title)s.%(ext)s'}
    for _v in _data:
        print(_v)
        url = _v['url']
        done = _v['done']
        _title = _v['title']  # 日本語字幕
        if done and _title != None:  # 形式
            print(f'文字お越し済み {_title}')
            continue
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    # 文字お越しの読み込み
            ret = ydl.download([url])
            info = ydl.extract_info(url, download=False)
            _title = info['title']
            if ret == 0:
                _v['done'] = True
                _v['title'] = _title
                print(f'[OK] {url} {_title}')
            else:
                print(f'[FAIL] {url} {_title}')
    youtube_links_path.write_text(json.dumps(_data, indent=2, ensure_ascii=False), encoding='utf-8')  # 成功した場合
    return (youtube_links_path,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 文字お越こし要約
    """)
    return


@app.cell
def _(
    LLM_gen,
    Path,
    json,
    load_dotenv,
    os,
    re,
    replace_chars,
    youtube_links_path,
):
    # パス設定
    caption_dir = Path('captions')
    summary_dir = Path('summary')
    summary_dir.mkdir(exist_ok=True)
    # if not caption_path.is_dir():
    #     raise
    load_dotenv()
    # gemini api keyの読み込み
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    _json_text = youtube_links_path.read_text(encoding='utf-8')
    _data = json.loads(_json_text)
    text_pattern = '\\d\\n.*\\n(.*)\\n'
    for p in caption_dir.iterdir():
    # print(data)
        p_str = str(p)
    # 正規表現を使いtextの抽出とLLMによる要約
        title_pattern = 'captions\\\\(.*).ja.srt'
        _title = re.search(title_pattern, p_str)[1]
        replaced_title = replace_chars(_title)  # print(p)
        text = p.read_text(encoding='utf-8')
        matchs = re.findall(text_pattern, text)
        text = '\n'.join(matchs)  # タイトル部分の抽出
        contents = '以下はyoutube動画の文字お越しをした文章です。要約してください。ただし、出力はMarkdown形式のみで行い、要約に関係ない説明文や前置きは一切書かないでください。見出し・箇条書きを適宜使って整理してください。\n\n' + text  # 危険文字の変換
        LLM_gen_flg = False
        name_match_flg = False  # 
        for _v in _data:
            _v['title'] = replace_chars(_v['title'])
            if replaced_title == _v['title']:
                LLM_gen_flg = _v['LLM_gen']
                print(f'titleが一致 : {replaced_title} : LLM_gen_flg={LLM_gen_flg!r}')
                name_match_flg = True
                if LLM_gen_flg == True:
                    print(f'要約済みです : {replaced_title}')
                else:
                    _v['LLM_gen'] = True
                    res = LLM_gen(contents)
                    print(f'{replaced_title},res={res!r}')
                    file_name = summary_dir / f'{replaced_title}.md'
                    file_name.write_text(res, encoding='utf-8')
        if not name_match_flg:  # print(v['title'])
            print(replaced_title)
    youtube_links_path.write_text(json.dumps(_data, indent=2, ensure_ascii=False), encoding='utf-8')
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Youtube Data API
    """)
    return


@app.cell
def _(load_dotenv, os):
    import requests

    def api_init():
        load_dotenv()
        API_KEY = os.environ['YOUTUBE_DATA_API_KEY']
        return API_KEY
    return api_init, requests


@app.cell
def _(requests):
    def get_playlist_items(API_KEY: str, playlist_id: str) -> dict:
        url = "https://www.googleapis.com/youtube/v3/playlistItems"
        r = requests.get(
            url,
            params={"part":"snippet", "playlistId":playlist_id, "key":API_KEY},
            timeout=20
        )
        r.raise_for_status()
        return r.json()
    return (get_playlist_items,)


@app.cell
def _(api_init, get_playlist_items):
    API_KEY = api_init()
    playlist_id = "PLrtfpfxtQtGusZ5mqhKki7ZyXJBGg9fQV"
    PlaylistItem = get_playlist_items(API_KEY,playlist_id)
    for item in PlaylistItem['items']:
        print(item['id'])


    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
