# 開発ワークフロー（共通）

Mac / Ubuntu 両方に効く共通ルール。OS 固有の厳しさ・緩さは `workflow-mac.md`
（Mac 厳格）と `workflow-ubuntu.md`（Ubuntu 緩め）に分けてある。

## PR 説明の作り方

- MUST 「背景」セクション（なぜこの変更が必要か）を含める。ユーザーの生のプロンプトを
  そのまま転記しない（Claude Code 生成マーカーの扱いは `git-mac.md` / `git-ubuntu.md` を参照）
- MUST AI が実装した PR は、説明の最上位に「Summary」節と「Items to Confirm / Review」節を
  置く。人間レビュワーが「何が変わったか」「何を特に見てほしいか（リスクある判断・仮定・
  未検証の挙動）」を最初に把握できる形にする。背景・実装詳細はその後
- SHOULD 設計変更・ドメインロジック変更・不具合の根本修正・方式選定・データ構造変更・
  パフォーマンス改善などの重い PR は、Context / Why / Decision / Alternatives / Risk の
  判断記録テンプレを本文に含める（推測で書かない。検討していない代替案は書かない）

## ドキュメントのメンテナンス

- MUST 変更後に README.md を確認し、正しい仕様を反映する
- MUST コマンド例、オプション、使い方の説明が正確であることを確認する
