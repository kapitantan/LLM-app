from pathlib import Path
import yt_dlp
import re
import json
from dotenv import load_dotenv
from google import genai
import os

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

# # youtubeの読み込み


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


# # 文字お越こし要約(parallel-version)

# ファイル出力なしで要約成功したバージョン
import asyncio 
title_list = [] # captionフォルダにあるタイトル名リスト
contents_dic = {} 

# パス設定
caption_dir= Path('captions')
summary_dir = Path('summary')
summary_dir.mkdir(exist_ok=True)
# gemini api keyの読み込み
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# 正規表現を使いtextの抽出とLLMによる要約
text_pattern = r"\d\n.*\n(.*)\n"
for p in caption_dir.iterdir(): 
    p_str = str(p) 
    title_pattern = r"captions\\(.*).ja.srt" 
    title = re.search(title_pattern, p_str)[1] # タイトル部分の抽出 
    replaced_title = replace_chars(title) # 危険文字の変換 
    text = p.read_text(encoding='utf-8') 
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
    title_list.append(replaced_title)
    contents_dic[title] = contents
    
async def llm_task(contents: str): 
    loop = asyncio.get_running_loop() 
    return await loop.run_in_executor(None, LLM_gen, contents) 

async def main(): 
    # tasks = [llm_task(contents_dic[title]) for title in contents_dic] 
    # results = await asyncio.gather(*tasks)
    # results = []
    # for title in contents_dic:
    #     res = await llm_task(contents_dic[title])  # ここで1本ずつ待つ
    #     results.append(res)

    json_text = youtube_links_path.read_text(encoding="utf-8")
    data = json.loads(json_text)
    # if len(data) == len(results):
    #     print(f"要約した合計は一致")
    # else:
    #     print(f"未要約が存在")
    #     raise RuntimeError

    # youtube_links.jsonに関するループ
    for v in data:
        LLM_gen_flg = False
        name_match_flg = False
        title = v['title']
        # title_listsに関するループ
        for t in title_list:
            if t == title:
                LLM_gen_flg = v['LLM_gen']
                name_match_flg = True
                # i = title_list.index(title)
                # res = results[i]
                print(f"titleが一致 : {title } : {LLM_gen_flg=}")
                break

        if not name_match_flg:
            print(f"!!! titleが不一致 : {title}")
            continue

        if LLM_gen_flg==False:
            res = await llm_task(contents_dic[title])  
            print(f"要約を出力します : {title}")
            file_name = summary_dir / f"{title}.md"
            print(file_name.name)
            file_name.write_text(res,encoding='utf-8')
            v['LLM_gen'] = True
        else:
            print(f"要約出力済みなのでスキップ :  {title}")
    youtube_links_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
        asyncio.run(main())
# await main()


