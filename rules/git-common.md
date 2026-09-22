# Git 操作ルール（共通）

Mac / Ubuntu 両方に常時適用されるルール。OS 固有の追加ルールは `git-mac.md`（Mac）と
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
- MUST リモートへの push、PR / Issue / Discussion の作成・更新・マージ・クローズは、その操作を自分が実行してよいかを確認してから行う。「〜で出したいです」「〜したい」はユーザー自身が行う意図のことがある。外向きの操作は取り消せないので、読み取れないときは聞く
- MAY 例外は、プロジェクトの CLAUDE.md に「外向きの操作は確認不要」と明記されているときだけ。個人の private リポジトリで、往復が増えるほうが損になる場合を想定している。宣言が無ければ確認する（仕事・課題提出・コミュニティのリポジトリは宣言しない）
  - 宣言があっても変わらないもの: 履歴を書き換える操作の禁止、`git add .` の禁止、取り消しにくい判断（公開、外部サービスの設定変更）を実行前に伝えること
- MUST `git add .` やディレクトリ一括 add をしない。ファイル名指定または glob
  （例: `git add docs/setup.md src/parser_*.go`）で対象を明示する
- MAY 読み取り専用操作（`git status`, `git diff`, `git log`）は自由に実行してよい
- SHOULD 意味のある変更ごとにコミットする
- SHOULD フィーチャーブランチを作成して PR/MR を出す
- MUST 個人用ローカルファイル（`CLAUDE.local.md` 等）を git 管理外にする場合、
  リポジトリの `.gitignore`（チーム共有）ではなく `.git/info/exclude`
  （ローカル限定・コミットされない）に追加する
