---
paths:
  - "**"
---

# Git 操作ルール

- NEVER ユーザーの明示的な許可なく `git commit`, `git push` 等を実行しない
- MUST 変更前に `git branch` または `git status` で現在のブランチを確認する
- NEVER `git add .` や `git add <directory>` は使わない。ファイルを個別に追加する
- NEVER 未追跡ファイルを削除しない
- NEVER `git push --force` は使わない
- NEVER `git rebase` は使わない
- MUST コミットメッセージにプレフィックスをつける: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- MAY 読み取り専用操作（`git status`, `git diff`, `git log`）は自由に実行してよい
- SHOULD 意味のある変更ごとにコミットする
- SHOULD フィーチャーブランチを作成してPR/MRを出す
- MUST 個人用ローカルファイル（`CLAUDE.local.md` 等）を git 管理外にする場合、リポジトリの `.gitignore`（チーム共有）ではなく `.git/info/exclude`（ローカル限定・コミットされない）に追加する
