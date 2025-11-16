# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.17.0",
#     "pyzmq",
# ]
# ///

# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo",
#     "pyzmq",
# ]
# ///

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
    import requests
    import marimo as mo
    from yt_dlp.utils import DownloadError
    return (
        DownloadError,
        Path,
        genai,
        json,
        load_dotenv,
        mo,
        os,
        re,
        requests,
        yt_dlp,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # summarize
    """)
    return


@app.cell
def _(Path, genai, json, load_dotenv, os, re, yt_dlp):
    def load_gemini_api_key():
        """
        Gemini APIキーをdotenvから読み込む
         引数: なし
         返り値: str 取得したAPIキー文字列
        """
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        return gemini_api_key


    def LLM_gen(contents: str) -> str:
        """
        Geminiでプロンプトからテキストを生成する
         引数: contents(str) LLMに渡す文章
         返り値: str モデルからの応答テキスト
        """
        client = genai.Client()

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=contents
        )
        return response.text


    # 危険な文字の除去
    def replace_chars(s: str) -> str:
        """
        ファイル名に使えない文字を安全な文字へ置換する
         引数: s(str) 変換対象の文字列
         返り値: str 置換後の文字列
        """
        remove_chars = '\\/:*?"<>|￥＜＞｜'  # 削除対象文字
        table = str.maketrans({ch: "-" for ch in remove_chars})
        s2 = s.translate(table)
        s3 = s2.replace(" ", "")
        return s3
        # TODO:srtファイルを削除したときにjsonファイルのdoneを全てfalseに修正する関数

    BACE_PATH = Path(__file__).parent
    YT_LINKS_PATH = BACE_PATH / "youtube_links.json"


    def save_json(url: str) -> bool:
        """
        新しいYouTube URLをJSONに保存する
         引数: url(str) 追加対象のYouTubeリンク
         返り値: bool 検証と保存が完了したかどうか
        """
        # URLの簡易的なバリデーション
        _YT_REGEX = re.compile(
            r"^https://www\.youtube\.com/watch\?v=([0-9A-Za-z_-]+)(?:&[^\s#]*)?$"
        )
        # re.compile(
        #     r"^(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w\-]{11})(?:$|[&#?])"
        # )
        match = _YT_REGEX.search(url.strip())
        if not match:
            print(f"Invalid YouTube URL")
            return False
        else:
            print(f" Validation OK")
            video_id = match.group(1)
        # JSON初期値で保存、既知のURLならスキップする
        text = YT_LINKS_PATH.read_text(encoding="utf-8")
        # print(text)
        youtube_link = json.loads(text)
        exist_flg = False
        for var in youtube_link:
            match = _YT_REGEX.search(var["url"].strip())
            id = match.group(1)
            if video_id == id:
                print(f"{video_id=}")
                print(f"{var['title']=}")
                print(f"{var['url']=},{id=}")
                exist_flg = True
                break
        if exist_flg:
            print("save skip")
            return True

        print("今から初期値で保存します")
        add_url = {"url": url, "done": False, "title": None, "LLM_gen": False}
        youtube_link.append(add_url)
        text = json.dumps(youtube_link, ensure_ascii=False, indent=2)
        YT_LINKS_PATH.write_text(text, encoding="utf-8")
        return True
    def summarize_json() -> None:
        """
        JSON設定に従って字幕取得と要約生成を行う
         引数: なし
         返り値: None 実行のみで値は返さない
        """
        # jsonファイルのパス設定
        youtube_links_file_name = "youtube_links.json"
        youtube_links_path = Path(youtube_links_file_name)
        json_text = youtube_links_path.read_text(encoding="utf-8")
        data = json.loads(json_text)
        _ydl_opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["ja"],  # 日本語字幕
            "subtitlesformat": "srt",  # 形式
            "outtmpl": "captions/%(title)s.%(ext)s",
        }

        # 文字お越しの読み込み
        for v in data:
            print(v)
            url = v["url"]
            done = v["done"]
            title = v["title"]

            if done and title != None:
                print(f"文字お越し済み {title}")
                continue
            with yt_dlp.YoutubeDL(_ydl_opts) as ydl:
                ret = ydl.download([url])
                info = ydl.extract_info(url, download=False)
                title = info["title"]
                if ret == 0:  # 成功した場合
                    v["done"] = True
                    v["title"] = title
                    print(f"[OK] {url} {title}")
                else:
                    print(f"[FAIL] {url} {title}")

        youtube_links_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # パス設定
        caption_dir = Path("captions")
        summary_dir = Path("summary")
        summary_dir.mkdir(exist_ok=True)

        json_text = youtube_links_path.read_text(encoding="utf-8")
        data = json.loads(json_text)
        # print(data)

        # 正規表現を使いtextの抽出とLLMによる要約
        text_pattern = r"\d\n.*\n(.*)\n"
        for p in caption_dir.iterdir():
            # print(p)
            p_str = str(p)
            title_pattern = r"captions\\(.*).ja.srt"
            print(p_str)
            try:
                title = re.search(title_pattern, p_str)[1]  # タイトル部分の抽出
            except TypeError as e:
                print(f"error:{e}")
                continue
            title = replace_chars(title)  # 危険文字の変換

            text = p.read_text(encoding="utf-8")  #
            matchs = re.findall(text_pattern, text)
            text = "\n".join(matchs)
            contents = (
                "以下はyoutube動画の文字お越しをした文章です。"
                "要約してください。"
                "ただし、出力はMarkdown形式のみで行い、"
                "要約に関係ない説明文や前置きは一切書かないでください。"
                "見出し・箇条書きを適宜使って整理してください。\n\n" + text
            )

            LLM_gen_flg = False
            name_match_flg = False
            for v in data:
                # print(v['title'])
                v["title"] = replace_chars(v["title"])
                if title == v["title"]:
                    LLM_gen_flg = v["LLM_gen"]
                    print(f"titleが一致 : {title} : {LLM_gen_flg=}")
                    name_match_flg = True

                    if LLM_gen_flg == True:
                        print(f"要約済みです : {title}")
                    else:
                        v["LLM_gen"] = True
                        res = LLM_gen(contents)
                        print(f"{title},{res=}")

                        file_name = summary_dir / f"{title}.md"
                        file_name.write_text(res, encoding="utf-8")
            if not name_match_flg:
                print(title)
        youtube_links_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    def _parse_json_payload(payload: str) -> list[dict[str, str]]:
        """
        LLM応答文字列からJSON形式のクイズ配列を抽出する
         引数: payload(str) LLMからの応答テキスト
         返り値: list[dict[str,str]] 抽出に成功したエントリ一覧
        """
        text_response = payload.strip()
        try:
            parsed = json.loads(text_response)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

        code_block = re.search(
            r"```(?:json)?\s*(.*?)```", text_response, re.DOTALL
        )
        if code_block:
            try:
                parsed = json.loads(code_block.group(1))
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass

        array_match = re.search(r"(\[.*\])", text_response, re.DOTALL)
        if array_match:
            try:
                parsed = json.loads(array_match.group(1))
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass

        return []
    def make_quiz(markdown_text: str, n: int) -> list[tuple[str, str]]:
        """
        要約Markdownを基にGeminiでクイズQAを生成する
         引数: markdown_text(str) 出題元, n(int) 作成数
         返り値: list[tuple[str,str]] 生成したQ/Aペア
        """
        markdown = markdown_text.strip()
        if not markdown or n <= 0:
            return []

        prompt = (
            "以下のMarkdown形式の文章を読んで、その内容を理解しているか確認する日本語のクイズを"
            f"{n}問作成してください。"
            "各出力要素はJSON形式で、キーは必ず'Q'と'A'のみを使用し、値に問題文と解答を入れてください。"
            "問題は文章中の事実や要点に基づき、単純な言い換えではなく理解度を確かめる内容にしてください。"
            "JSON以外の余計な文字列やコードフェンスは出力しないでください。"
            "\n\n[Markdown]\n"
            f"{markdown}\n"
        )

        raw_response = LLM_gen(prompt)

        quiz_items = _parse_json_payload(raw_response)

        qa_list: list[tuple[str, str]] = []
        for qa in quiz_items:
            if not isinstance(qa, dict):
                continue
            question = qa.get("Q")
            answer = qa.get("A")
            if not question or not answer:
                continue
            qa_list.append((str(question).strip(), str(answer).strip()))
            if len(qa_list) >= n:
                break
        print(qa_list)
        return qa_list
    return LLM_gen, YT_LINKS_PATH, replace_chars, save_json


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Youtube Data API
    """)
    return


@app.cell
def _(load_dotenv, os, requests):
    def api_init():
        """
        dotenvからYouTube Data APIキーを読み込む
         引数: なし
         返り値: str YouTube Data APIキー
        """
        load_dotenv()
        API_KEY = os.environ["YOUTUBE_DATA_API_KEY"]
        return API_KEY
    def get_playlist_items(API_KEY: str, playlist_id: str) -> dict:
        """
        YouTube Data APIで指定プレイリストのアイテムを取得する
         引数: API_KEY(str) 認証キー, playlist_id(str) 対象プレイリストID
         返り値: dict APIレスポンスJSON
        """
        url = "https://www.googleapis.com/youtube/v3/playlistItems"
        r = requests.get(
            url,
            params={
                "part": "snippet",
                "playlistId": playlist_id,
                "maxResults": 50,
                "key": API_KEY,
            },
            timeout=20,
        )
        r.raise_for_status()
        return r.json()
    def make_youtube_url(videoId: str) -> str:
        return "https://www.youtube.com/watch?v=" + videoId
    return api_init, get_playlist_items, make_youtube_url


@app.cell
def _(mo):
    mo.md(r"""
    # 実行セル
    """)
    return


@app.cell
def _(api_init, get_playlist_items, make_youtube_url, save_json):
    def get_playlist_url_list(_playlist_id: str) -> list:
        """ """
        API_KEY = api_init()
        PlaylistItem = get_playlist_items(API_KEY, _playlist_id)
        _playlist_video_url_list = []
        print(PlaylistItem["items"][0]["snippet"].keys())
        for _item in PlaylistItem["items"]:
            _videoId = _item["snippet"]["resourceId"]["videoId"]
            _playlist_video_url_list.append(make_youtube_url(_videoId))
        return _playlist_video_url_list


    # プレイリストのvideoIdを取得
    playlist_id = "PLrtfpfxtQtGusZ5mqhKki7ZyXJBGg9fQV"
    playlist_video_url_list = get_playlist_url_list(playlist_id)

    # jsonファイルに保存
    for _url in playlist_video_url_list:
        save_json(_url)
    return


@app.cell
def _(DownloadError, YT_LINKS_PATH, json, yt_dlp):
    # json読み込み
    _json_text = YT_LINKS_PATH.read_text(encoding="utf-8")
    data = json.loads(_json_text)

    print(len(data), data)
    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["ja"],
        "subtitlesformat": "srt",
        "outtmpl": "captions/%(title)s.%(ext)s",
    }
    # jsonから読み込んだ情報をループで回して文字お越しを
    for _v in data:
        # print(_v)
        url = _v["url"]
        done = _v["done"]
        _title = _v["title"]  # 日本語字幕
        if done and _title != None:  # 形式
            print(f"文字お越し済み {_title}")
            continue
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 文字お越しの読み込み
            try:
                ret = ydl.download([url])
                info = ydl.extract_info(url, download=False)
                print(f"{info.keys()}")
                _title = info["title"]
                print(_title)
                if ret == 0:
                    _v["done"] = True
                    _v["title"] = _title
                    print(f"文字お越し成功： {url} {_title}")
                else:
                    print(f"文字お越し失敗： {url} {_title}")
            except DownloadError as e:
                print("ダウンロードエラー：", e)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # 文字お越こし要約
    """)
    return


@app.cell
def _(LLM_gen, Path, YT_LINKS_PATH, json, load_dotenv, os, re, replace_chars):
    # パス設定
    caption_dir = Path("captions")
    summary_dir = Path("summary")
    summary_dir.mkdir(exist_ok=True)
    # if not caption_path.is_dir():
    #     raise
    load_dotenv()
    # gemini api keyの読み込み
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    _json_text = YT_LINKS_PATH.read_text(encoding="utf-8")
    _data = json.loads(_json_text)
    text_pattern = "\\d\\n.*\\n(.*)\\n"
    for p in caption_dir.iterdir():
        # print(data)
        p_str = str(p)
        # 正規表現を使いtextの抽出とLLMによる要約
        title_pattern = "captions\\\\(.*).ja.srt"
        _title = re.search(title_pattern, p_str)[1]
        replaced_title = replace_chars(_title)  # print(p)
        text = p.read_text(encoding="utf-8")
        matchs = re.findall(text_pattern, text)
        text = "\n".join(matchs)  # タイトル部分の抽出
        contents = (
            "以下はyoutube動画の文字お越しをした文章です。要約してください。ただし、出力はMarkdown形式のみで行い、要約に関係ない説明文や前置きは一切書かないでください。見出し・箇条書きを適宜使って整理してください。\n\n"
            + text
        )  # 危険文字の変換
        LLM_gen_flg = False
        name_match_flg = False  #
        for _v in _data:
            _v["title"] = replace_chars(_v["title"])
            if replaced_title == _v["title"]:
                LLM_gen_flg = _v["LLM_gen"]
                print(
                    f"titleが一致 : {replaced_title} : LLM_gen_flg={LLM_gen_flg!r}"
                )
                name_match_flg = True
                if LLM_gen_flg == True:
                    print(f"要約済みです : {replaced_title}")
                else:
                    try:
                        res = LLM_gen(contents)
                        # print(f"{replaced_title},res={res!r}")
                        file_name = summary_dir / f"{replaced_title}.md"
                        file_name.write_text(res, encoding="utf-8")
                        _v["LLM_gen"] = True
                        print(f"{file_name}要約成功")
                    except Exception as e:
                        print(f"{replaced_title} 要約失敗：{e}")
        if not name_match_flg:  # print(v['title'])
            print(replaced_title)
    YT_LINKS_PATH.write_text(
        json.dumps(_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return


if __name__ == "__main__":
    app.run()
