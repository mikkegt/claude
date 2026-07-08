---
paths:
  - "/home/**"
---

# Git 操作ルール（Ubuntu・緩め）

共通ルールは `git-common.md` を参照。ここは Ubuntu 側で緩めるルール。実験的な
自律実行を許容するが、履歴書き換え禁止（共通ルール）と未追跡ファイル削除禁止
（共通ルール）は変わらず適用される。

- MAY `git commit`, `git push` は自律的に実行してよい（内容が妥当なら）
- MAY `git add .` / `git add <directory>` を使ってよい
- MAY コミットメッセージや PR/MR 本文に Claude Code 生成マーカーを含めてよい
