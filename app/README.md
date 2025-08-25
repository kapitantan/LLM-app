# 概要
1. obsidianのsync your kindle highlight プラグインを使い、kindle書籍でハイライトした箇所を抽出
1. 開発中のプログラムを実行することで、ハイライト文章の要約と問題の作成を行いMarkdownファイルとして出力する
1. 今後の展望として学習効果が最大になるような出題を目指す
##  入力（Kindleハイライトmdファイル）
- mdファイルを想定、mdファイル以外は対応外
    - エクスポート形式としてhtml,csvなどがあるらしいが、obsidianのプラグインを活用するとmdファイルとして取得できるのでこの方法を採用。
- 取り込み時の重複・ノイズ対策
- ~~70文字未満の断片や辞書的見出しのみは除外（しきい値可変）~~
- ~~同一文の重複をMD5で排除~~
## 生成物（Obsidianで使うMarkdown）
- 1ファイル＝1冊（章ごとにセクション分割可）
- YAML Frontmatterを必ず付与（検索・集計しやすさ向上）
- ~~出力フォーマット：トグル表示に以下を採用~~
        <details><summary>問題</summary>回答</details>
- 見出しでもfoldができるので変更、ホットキーの割り当てが必要
## 問題タイプ（段階導入）
1. 要点QA（短答式）
1. Cloze（穴埋め）：重要語を [...] に置換（語尾ヒント可）
1. 二択/三択（フェイントは同章語彙から自動抽出）

について、まずはランダムに問題を作成
## フォルダ構成
```
kindle
├─ highlight/     # 入力：プラグインが吐く元ハイライト（複数冊）
│  └─ ...
├─ summary/       # 生成：ハイライトを元に生成した要約
│  └─ ...
├─ problem_bank/  # 生成：要約を元に問題を生成、1問=1ノート（将来の拡張＆SRSに強い）
│  ├─ <uuid_省略した問題>.md         # Frontmatterでメタ管理
│  └─ ...
├─ indexes/                         # 索引・ランダム出題の中枢
│  ├─ Problem Deck.md               # 全書籍横断でランダム出題するノート
│  ├─ Book List.md                  # 本と進捗の一覧
│  └─ Queries.md                    # 検索・Dataviewテンプレ置き場
├─ _scripts/                        # プログラム置き場（リポジトリ管理）
│  ├─ ingest.py                     # ① 取り込み＆正規化＆MD5重複排除
│  ├─ summarize_and_generate.py     # ② 要約→問題生成（Gemini 2.5 Flash）
│  ├─ build_book_files.py           # ③ 書籍ファイル組み立て（章セクション）
│  ├─ split_to_problem_bank.py      # ④ 問題を1問=1ノートに分割・保存
│  ├─ shuffle_deck.py               # ⑤ デッキ用のランダムリンクを更新
│  └─ utils.py                      # 正規化/MD5/Frontmatterユーティリティ
└─ templates/                       # Templaterや雛形
   ├─ problem_note.md
   └─ book_note.md
```
## モデル利用
- 生成は gemini-2.5-flash で十分高速
- トークン節約：章ごとチャンク + **箇条書きの要約→問題化 の2段プロンプ**
- 生成温度：要点QAは 0.2、Cloze/選択式は 0.4 など タイプ別に制御
## 学習計画（SRS:spaced repetition system(間隔反復システム)）
今後の展望
<!-- - Frontmatterに学習予定を格納（手動でも扱いやすい）
- review_plan:
  - +1d
  - +3d
  - +7d
  - +14d
- 実際の通知はObsidianの検索フィルタ運用でOK（プラグイン不要で始める） -->