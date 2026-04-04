---
name: issue-index
description: Issue一覧が必要な場面で、gh APIの代わりにローカルキャッシュ(.issue-index.json)を参照する。トークン節約のため、gh issue listを直接叩かない。
---

# Issue Index

Issue一覧が必要なとき、`gh issue list` の代わりにローカルの `.issue-index.json` を `Read` する。

## いつ使うか

他のSkill（read-article等）や朝ルーティンでIssue一覧が必要になったとき、自動的にこのスキルの方針に従う。

## 手順

1. `.issue-index.json` を `Read` する
2. ファイルが存在しない場合、sync.sh を実行して作成する:
   ```
   bash ~/workspace/github.com/mikkegt/claude/skills/issue-index/sync.sh .
   ```
3. `updated_at` が24時間以上前の場合も、同様にsync.shを実行してから読む

## フォーマット

```json
{
  "updated_at": "2026-04-05T12:00:00Z",
  "repo": "mikkegt/Jarvis",
  "issues": [
    {
      "number": 83,
      "title": "PTA静的サイトキットを構築する",
      "labels": ["self", "someday"],
      "state": "OPEN",
      "status": "Todo",
      "deadline": "2026-04-10"
    }
  ]
}
```

## 注意

- `gh issue list` を直接叩かない。必ずインデックスを経由する
- インデックスはセッション開始時にhookで自動更新される
- 最新のIssueが反映されていない可能性がある場合のみ、手動でsync.shを実行する
