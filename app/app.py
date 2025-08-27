# %% [markdown]
# # import

# %%
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from google import genai
import json

# %% [markdown]
# # 関数定義

# %%
def LLM_gen(contents: str) -> str:
    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents= contents
    )
    return response.text

# %% [markdown]
# # ハイライトの読み込みと要約

# %%
# APIKEYの読み込み
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# ハイライトディレクトリの読み込み
highlight_dir = Path("highlight")
if not highlight_dir.is_dir():
        raise NotADirectoryError(f"{highlight_dir} is not a directory")
for f in highlight_dir.iterdir():
    text = f.read_text(encoding="utf-8")
    lines = text.splitlines()

    # 書籍のプロティの作成
    property = {}
    for l in lines:
        if 'title' in l:
            title = l.split(':')[1]
            title = title.strip() # 空白を除去しないとエラーになる
        if 'author' in l:
            author = l.split(':')[1]

    property['title'] = title
    property['author'] = author
    property['tags'] = ['kindle', 'quize']

    frontmatter = '---\n'
    for v in property:
        if type(property[v]) == list:
            frontmatter += v + ': ' + json.dumps(property[v]) + '\n'
        if type(property[v]) == str:
            frontmatter += v + ': ' + property[v] + '\n'
    frontmatter += '---\n'
    # print(frontmatter)
    
    # Highlight箇所の抽出
    highlightAfterPattern = r"##\s*Highlights\n*(.*)—\slocation"
    dashWrappedPattern = r"---\n*(.*)\n*—\slocation"
    matches = re.findall(highlightAfterPattern, text)
    matches += re.findall(dashWrappedPattern, text)
    # print(matches)

    highlightMarkdown = ''
    for text in matches:
        highlightMarkdown += '- ' + text + '\n'
    # print(highlightMarkdown)

    # mdファイルの要約
    contents= (
            "以下は書籍のハイライトをMarkdown形式にまとめたものです。"
            "要約してください。"
            "ただし、出力はMarkdown形式のみで行い、"
            "要約に関係ない説明文や前置きは一切書かないでください。"
            "見出し・箇条書きを適宜使って整理してください。\n\n"
            + highlightMarkdown
        )
    res = LLM_gen(contents)
    # print(res)

    # 要約をMarkdownファイルとして出力
    save_dir = Path("summary")
    save_dir.mkdir(exist_ok=True)
    filename = save_dir/f"{title}.md"
    print(filename)
    text = frontmatter + res
    filename.write_text(text,encoding="utf-8")

# %% [markdown]
# # 問題生成

# %%
# 問題保管ディレクトリの作成
save_dir = Path("problem_bank")
save_dir.mkdir(exist_ok=True)

summary_dir = Path("summary")
if not summary_dir.is_dir():
        raise NotADirectoryError(f"{summary_dir} is not a directory")

# 要約の読み込みと問題の作成
for f in summary_dir.iterdir():
        text = f.read_text(encoding="utf-8")
        # print(text)
        pattern = r"---\n(.*)\n(.*)\n(.*)\n---"
        matches = re.search(pattern, text)
        frontmatter = matches.group(0)
        title = matches.group(1).split(':')[1]
        title = title.strip() # 空白を除去しないとエラーになる
        # print(frontmatter)

        contents = (
        "以下は書籍の一部を要約した文章です。"
        "この要約の内容を網羅するように問題を作成してください。"
        "出題は必ず複数の観点を含めてください（定義確認・理由説明・比較・応用シナリオ）。"
        "各問題は必ずMarkdown形式で次のフォーマットに従ってください：\n\n"
        "### （ここに問題文そのものを一つだけ書く）\n"
        "**解答**　（ここに解答を書く）\n"
        "**解説**　（ここに解説を書く）\n\n"
        "問題作成に関係ない説明文や前置きは一切書かないでください。\n\n"
        + text
        )

        res = LLM_gen(contents)
        # print(res)

        file_path = save_dir / Path(title+".md")
        file_path.write_text(frontmatter + "\n" + res, encoding="utf-8")




