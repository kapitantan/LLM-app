# %% [markdown]
# # import

# %%
from pathlib import Path
import yt_dlp
import re
import json
from dotenv import load_dotenv
from google import genai
import os

# %% [markdown]
# # 関数定義

# %%
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

# %% [markdown]
# # youtubeの読み込み

# %%
# jsonファイルの読み込み
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

# %% [markdown]
# # 文字お越こし要約

# %%
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


