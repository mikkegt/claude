---
name: issue-index
description: Issueインデックスの同期・参照。gh APIを毎回叩く代わりにローカルキャッシュを使ってトークンを節約する。
argument-hint: <sync|status>
---

# Issue Index

ローカルの `.issue-index.json` を管理するスキル。

## 引数

- `sync` — インデックスを最新に更新する
- `status` または引数なし — インデックスの状態（最終更新日時、件数）を表示

## 手順

### sync の場合

1. プロジェクトルートの `.env.issue-index` を確認する。なければエラーを表示して終了
2. 以下のコマンドを実行:
   ```
   bash ~/workspace/github.com/mikkegt/claude/skills/issue-index/sync.sh .
   ```
3. 完了メッセージを表示

### status の場合（デフォルト）

1. `.issue-index.json` を `Read` する。なければ「未作成。`/issue-index sync` で作成してください」と表示
2. `updated_at` と Issue 件数を表示
3. 最終更新から24時間以上経過していたら、sync を提案

## 他のSkillからの利用方法

Issue一覧が必要な場合、`gh issue list` の代わりに `.issue-index.json` を `Read` する。

```
# 変更前
gh issue list --state open

# 変更後
Read .issue-index.json
```

インデックスが古い（24時間以上）場合は、先に sync を実行してから読む。
