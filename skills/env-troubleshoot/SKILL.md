---
name: env-troubleshoot
description: 開発環境のトラブル調査を支援する。JetBrains IDE (CLion/GoLand/PyCharm/WebStorm) のフォーマッターやショートカットが効かない、clangd など言語サーバーが起動しない、Homebrew が Rosetta エラーを出す、Mac の arch が i386 になっている等の症状で起動。トリガー例 "フォーマッターが効かない", "Reformat Code 効かない", "⌥⌘L 効かない", "clangd 動かない", "アクション準備中", "brew Rosetta", "Cannot install under Rosetta 2", "arch が i386"。
argument-hint: "[症状キーワード（任意）: formatter | clangd | rosetta | terminal-arch ...]"
---

# 環境トラブル調査

開発環境系のトラブル（IDE のフォーマッター不調、言語サーバー起動失敗、Homebrew/Rosetta 問題等）を、既存の調査メモに沿って切り分ける。

## 知識ソース

実体は `~/workspace/github.com/mikkegt/claude/docs/env-troubleshooting.md` にある。Skill はその案内役なので、まずこのファイルを Read して最新の手順を取得する（メモは追記されていく前提）。

## 手順

1. `~/workspace/github.com/mikkegt/claude/docs/env-troubleshooting.md` を Read する
2. 引数 `$ARGUMENTS` を確認する
   - 空欄: ユーザーに「どの症状ですか？」と聞く（候補を箇条書きで提示）
   - 値あり: 下表のマッピングで該当セクションへ直行
3. 該当セクションのチェック手順を**1ステップずつ**ユーザーと進める（一気に全部書かない、ユーザーの回答を待つ）
4. 解決したら「メモに追記すべき新情報があるか」を判断し、あれば `docs/env-troubleshooting.md` への追記を提案する

## 引数マッピング

| 引数キーワード | 該当セクション |
|---------------|---------------|
| `formatter`, `reformat`, `フォーマッター` | JetBrains 全般 → フォーマッターが効かない |
| `clangd`, `clion`, `アクション準備中` | CLion (C/C++) 固有 |
| `gopls`, `goland`, `gofmt` | GoLand (Go) 固有 |
| `pycharm`, `black`, `ruff` | PyCharm (Python) 固有 |
| `webstorm`, `prettier` | WebStorm (JS/TS) 固有 |
| `rosetta`, `brew` | Mac 環境 → Homebrew Rosetta エラー |
| `arch`, `terminal-arch`, `i386` | Mac 環境 → ターミナルの arch |

## 進行のコツ

- 一度に全手順を提示しない。1ステップ実行 → 結果を聞く → 次へ、の対話形式
- ユーザーの環境で再現しないステップは飛ばす（例: ⌥⌘L で動いたらキーマップ確認は不要）
- 既存メモにない症状・対処に当たったら、解決後に「追記しますか？」と提案する。メモが育つことが Skill の価値

## 知識重複の回避

このファイル（SKILL.md）に具体的な対処手順を書かない。手順はすべて `docs/env-troubleshooting.md` 側に置き、Skill は参照とフロー制御だけを担う。両方に書くと更新漏れの温床になる。
