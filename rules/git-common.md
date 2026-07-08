# Git 操作ルール（共通）

Mac / Ubuntu 両方で常時効くルール。OS 固有の追加ルールは `git-mac.md`（Mac）と
`git-ubuntu.md`（Ubuntu）に分けてある。

- MUST 変更前に `git branch` または `git status` で現在のブランチを確認する
- NEVER 未追跡ファイルを削除しない（作業中ファイルの損失防止）
- NEVER Git 履歴を書き換える操作をしない:
  - `git push --force` / `git push --force-with-lease`
  - `git rebase`（`-i` 対話含む）
  - push 済みコミットへの `git commit --amend`
  - `git reset --hard <過去のコミット>`（HEAD より過去に戻す）
  - `git filter-branch` / `git filter-repo`
- MUST コミットメッセージにプレフィックスをつける: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- MAY 読み取り専用操作（`git status`, `git diff`, `git log`）は自由に実行してよい
- SHOULD 意味のある変更ごとにコミットする
- SHOULD フィーチャーブランチを作成して PR/MR を出す
- MUST 個人用ローカルファイル（`CLAUDE.local.md` 等）を git 管理外にする場合、
  リポジトリの `.gitignore`（チーム共有）ではなく `.git/info/exclude`
  （ローカル限定・コミットされない）に追加する
