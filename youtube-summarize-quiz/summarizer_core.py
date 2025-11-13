from pathlib import Path
import yt_dlp
import re
import json
from dotenv import load_dotenv
from google import genai
import os
import json

def load_gemini_api_key():
    """GEMINI_API_KEYを.envから読み込む。

    Returns:
        str | None: 環境変数に設定されていればAPIキー、存在しない場合はNone。
    """

    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    return gemini_api_key

def LLM_gen(contents: str) -> str:
    """Geminiを使って文章を生成する。

    Args:
        contents (str): Geminiに渡す完全なプロンプト。

    Returns:
        str: 生成結果として返されるテキスト。
    """

    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents= contents
    )
    return response.text

def replace_chars(s: str) -> str:
    """ファイル名に使えない文字を安全な文字へ置換する。

    Args:
        s (str): 元のタイトルやファイル名候補。

    Returns:
        str: 危険文字を除去した文字列。
    """

    remove_chars = '\\/:*?"<>|￥＜＞｜'  # 削除対象文字
    table = str.maketrans({ch: '-' for ch in remove_chars})
    s2 = s.translate(table)
    s3 = s2.replace(" ","")
    return s3
# TODO:srtファイルを削除したときにjsonファイルのdoneを全てfalseに修正する関数

YT_LINKS_PATH = Path(__file__).parent / "youtube_links.json"
def save_json(url: str) -> bool:
    """YouTube URLをJSONに追記する（既知ならスキップ）。

    Args:
        url (str): 保存対象のYouTube動画URL。

    Returns:
        bool: バリデーション成功でTrue、URLが不正な場合はFalse。
    """

    # 簡易的なバリデーション
    _YT_REGEX = re.compile(r"^(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w\-]{11})(?:$|[&#?])")
    match = _YT_REGEX.search(url.strip())
    if not match:
        print(f"Invalid YouTube URL")
        return False
    else:
        print(f"問題なし")
        video_id = match.group(1)
    # JSON初期値で保存、既知のURLならスキップする
    text = YT_LINKS_PATH.read_text(encoding='utf-8')
    # print(text)
    youtube_link = json.loads(text)
    exist_flg = False
    for var in youtube_link:
        match = _YT_REGEX.search(var['url'].strip())
        id = match.group(1)
        if video_id == id:
            print(f"{video_id=}")
            print(f"{var['title']=}")
            print(f"{var['url']=},{id=}")
            exist_flg = True
            break
    if exist_flg:
        print('save skip')
        return True
    
    print('今から初期値で保存します')
    add_url =  {
        "url": url,
        "done": False,
        "title": None,
        "LLM_gen": False
    }
    youtube_link.append(add_url)
    text = json.dumps(youtube_link, ensure_ascii=False, indent=2)
    YT_LINKS_PATH.write_text(text, encoding='utf-8')
    return True

def summarize_json() -> None:
    """未処理のYouTubeリンクに対して字幕取得と要約生成を行う。

    Returns:
        None: 処理結果はファイルシステム（captions/・summary/・JSON）に反映される。
    """

    # jsonファイルのパス設定
    youtube_links_file_name = "youtube_links.json"
    youtube_links_path = Path(youtube_links_file_name)
    json_text = youtube_links_path.read_text(encoding="utf-8")
    data = json.loads(json_text)
    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["ja"],     # 日本語字幕
        "subtitlesformat": "srt",     # 形式
        "outtmpl": "captions/%(title)s.%(ext)s" 
    }
    

    # 文字お越しの読み込み
    for v in data:
        print(v)
        url = v['url']
        done = v['done']
        title = v['title']
        
        if done and title!=None:
            print(f"文字お越し済み {title}")
            continue
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ret = ydl.download([url])
            info = ydl.extract_info(url, download=False)
            title = info['title']
            if ret == 0: # 成功した場合
                v['done'] = True
                v['title'] = title
                print(f"[OK] {url} {title}")
            else:
                print(f"[FAIL] {url} {title}")

    youtube_links_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # パス設定
    caption_dir= Path('captions')
    summary_dir = Path('summary')
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
            title = re.search(title_pattern, p_str)[1] # タイトル部分の抽出
        except TypeError as e:
            print(f"error:{e}")
            continue
        title = replace_chars(title) # 危険文字の変換

        text = p.read_text(encoding='utf-8') # 
        matchs = re.findall(text_pattern, text)
        text = '\n'.join(matchs)
        contents= (
            "以下はyoutube動画の文字お越しをした文章です。"
            "要約してください。"
            "ただし、出力はMarkdown形式のみで行い、"
            "要約に関係ない説明文や前置きは一切書かないでください。"
            "見出し・箇条書きを適宜使って整理してください。\n\n"
            + text
        )
        
        LLM_gen_flg = False
        name_match_flg = False
        for v in data:
            # print(v['title'])
            v['title'] = replace_chars(v['title'])
            if title == v['title']:
                LLM_gen_flg = v['LLM_gen']
                print(f"titleが一致 : {title } : {LLM_gen_flg=}")
                name_match_flg = True
                
                if LLM_gen_flg==True:
                    print(f"要約済みです : {title}")
                else:
                    v['LLM_gen'] = True
                    res = LLM_gen(contents)
                    print(f"{title},{res=}")
                
                    file_name = summary_dir / f"{title}.md"
                    file_name.write_text(res,encoding='utf-8')
        if not name_match_flg:
            print(title)
    youtube_links_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def _parse_json_payload(payload: str) -> list[dict[str, str]]:
    """GeminiレスポンスからJSON配列をベストエフォートで抽出する。

    Args:
        payload (str): コードフェンス等を含む可能性がある生テキストレスポンス。

    Returns:
        list[dict[str, str]]: `{"Q": ..., "A": ...}`形式の辞書リスト。解析に失敗した場合は空リスト。
    """

    text_response = payload.strip()
    try:
        parsed = json.loads(text_response)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    code_block = re.search(r"```(?:json)?\s*(.*?)```", text_response, re.DOTALL)
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
    """要約MarkdownからGemini経由でクイズを生成する。

    Args:
        markdown_text (str): クイズの根拠となるMarkdown本文。
        n (int): 生成したい設問ペアの数。

    Returns:
        list[tuple[str, str]]: 最大`n`件の(Question, Answer)タプル。
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

    

# # youtubeの読み込み
# jsonファイルの読み込み
def app():
    """コマンドラインから全文書き起こしと要約生成を行う補助関数。

    Returns:
        None: 入出力はファイル更新と標準出力ログで確認する。
    """

    youtube_links_file_name = "youtube_links.json"
    youtube_links_path = Path(youtube_links_file_name)
    # if not youtube_links_path.exists():
    #     raise 
    json_text = youtube_links_path.read_text(encoding="utf-8")
    data = json.loads(json_text)

    ydl_opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["ja"],     # 日本語字幕
        "subtitlesformat": "srt",     # 形式
        "outtmpl": "captions/%(title)s.%(ext)s" 
    }

    # 文字お越しの読み込み
    for v in data:
        print(v)
        url = v['url']
        done = v['done']
        title = v['title']
        
        if done and title!=None:
            print(f"文字お越し済み {title}")
            continue
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ret = ydl.download([url])
            info = ydl.extract_info(url, download=False)
            title = info['title']
            if ret == 0: # 成功した場合
                v['done'] = True
                v['title'] = title
                print(f"[OK] {url} {title}")
            else:
                print(f"[FAIL] {url} {title}")

    youtube_links_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    # パス設定
    caption_dir= Path('captions')
    summary_dir = Path('summary')
    summary_dir.mkdir(exist_ok=True)
    # if not caption_path.is_dir():
    #     raise

    # gemini api keyの読み込み
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    json_text = youtube_links_path.read_text(encoding="utf-8")
    data = json.loads(json_text)
    # print(data)

    # 正規表現を使いtextの抽出とLLMによる要約
    text_pattern = r"\d\n.*\n(.*)\n"
    for p in caption_dir.iterdir():
        # print(p)
        p_str = str(p)
        title_pattern = r"captions\\(.*).ja.srt"
        title = re.search(title_pattern, p_str)[1] # タイトル部分の抽出
        title = replace_chars(title) # 危険文字の変換

        text = p.read_text(encoding='utf-8') # 
        matchs = re.findall(text_pattern, text)
        text = '\n'.join(matchs)
        contents= (
            "以下はyoutube動画の文字お越しをした文章です。"
            "要約してください。"
            "ただし、出力はMarkdown形式のみで行い、"
            "要約に関係ない説明文や前置きは一切書かないでください。"
            "見出し・箇条書きを適宜使って整理してください。\n\n"
            + text
        )
        
        LLM_gen_flg = False
        name_match_flg = False
        for v in data:
            # print(v['title'])
            v['title'] = replace_chars(v['title'])
            if title == v['title']:
                LLM_gen_flg = v['LLM_gen']
                print(f"titleが一致 : {title } : {LLM_gen_flg=}")
                name_match_flg = True
                
                if LLM_gen_flg==True:
                    print(f"要約済みです : {title}")
                else:
                    v['LLM_gen'] = True
                    res = LLM_gen(contents)
                    print(f"{title},{res=}")
                
                    file_name = summary_dir / f"{title}.md"
                    file_name.write_text(res,encoding='utf-8')
        if not name_match_flg:
            print(title)
    youtube_links_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


