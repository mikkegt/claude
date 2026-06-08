# `<dir-path>` — INDEX

最終更新: YYYY-MM-DD
ファイル数: N (+ archive/ に M ファイル)

> Claude Code が最初に読むファイル。
> 作業時はまず `current-task.md` を、Claude が過去レポートを探す時はここから該当ファイルを特定する。

---

## 🎯 まず最初に読むべきファイル

| ファイル | 内容 |
|---|---|
| [current-task.md](current-task.md) | 現在のタスク状態 |
| [<key-report>.md](<key-report>.md) | <重要な集約レポートがあればここに> |

---

## トピック別索引

<!-- Claude が「〜について何書いた?」を検索する用。
     トピック単位でファイルをグルーピングする。複数ファイルが分散していても 1 ジャンプで辿れるように。 -->

### <topic-1> (状態 / 関連 PR 番号など)

| 役割 | ファイル |
|---|---|
| 集約レポート (本体) | [<file>.md](<file>.md) |
| 検証方針 | [<file>.md](<file>.md) |
| 個人メモ | [<file>.md](<file>.md) |

### <topic-2>

| 役割 | ファイル |
|---|---|
| 設計背景 | [<file>.md](<file>.md) |
| 検証結果 | [<file>.md](<file>.md) |

<!-- 必要に応じて topic-3, topic-4 ... を追加 -->

---

## カテゴリ別 (命名規則ベース)

| プレフィックス | 用途 | 該当ファイル数 |
|---|---|---|
| `current-` | 現在進行中のタスク | 1 |
| `report-YYYYMMDD-` | 検証 / 週次 / 設計レポート | N |
| `mtg-(report-)?YYYYMMDD-` | MTG 議事録 + 要約 | N |
| `note-` | 個人備忘メモ | N |
| `slack-` | Slack 提案 / 共有用 | N |
| `todo-` | TODO リスト | N |
| (規約外) | 古いもの / 引き継ぎ系 | N |

---

## 命名規則

`<type>-YYYYMMDD-<slug>.md` (詳細は `~/workspace/github.com/mikkegt/claude/rules/docs.md` 参照)

---

## archive について

`archive/` には以下が入る:

- 3 ヶ月以上古いファイル
- 重複ファイル (`-draft.md`, `-MTG用.md` などの派生版)
- 集約レポートに統合された個別レポート
- 過去 archive

「過去にこういう検討があったはず」を辿りたい時は `ls archive/` で探す。

---

## このファイルのメンテ方針

- 手動メンテ (40 ファイル未満なら現実的)
- 新規レポート追加時に「トピック別索引」に追記
- 古いファイルを archive 化したら数を更新
- 半年ごとに見直し、INDEX 自体が機能不全になったら自動生成 Skill 化を検討

---

## 関連

- [MEMORY.md](<path-to-memory>) — Claude の永続記憶 (project-wide)
- [archive/](archive/) — 過去レポートのアーカイブ
- 整理ルール本体: `~/workspace/github.com/mikkegt/claude/rules/docs.md`
