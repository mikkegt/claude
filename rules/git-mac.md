---
paths:
  - "/Users/**"
---

# Git 操作ルール（macOS・厳格）

共通ルールは `git-common.md` を参照。ここは Mac 側で追加する厳格ルール。

- NEVER ユーザーの明示的な許可なく `git commit`, `git push` 等を実行しない
- NEVER `git add .` や `git add <directory>` は使わない。ファイルを個別に追加する
- NEVER コミットメッセージや PR/MR 本文に Claude Code 生成マーカーを含めない
  （例: `🤖 Generated with Claude Code` trailer、`Co-authored-by: Claude ...`）
