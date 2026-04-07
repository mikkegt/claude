---
name: transcript-analyzer
description: Claude Codeのセッションログ（~/.claude/projects/配下のJSONL transcripts）を集計し、ツール/スキルごとの呼び出し回数と失敗率を出す。「どのスキルがコケやすいか」を定量で把握してCLAUDE.md/MEMORY.md改善のループに供給する。
allowed-tools: Bash, Read
---

# transcript-analyzer

Claude Codeの過去セッションを集計してツール使用パターンと失敗率を可視化する。

## 背景

Claude Codeはセッションごとに `~/.claude/projects/<project>/<session-id>.jsonl` にtranscriptを自動保存する（`tool_use` / `tool_result` の対が含まれる）。これを集計すれば、人間の主観ではなく実データでスキルの改善ポイントを特定できる。

参考: [エージェントのログは安く、人間の介入は高い](https://qiita.com/masato_makino/items/5807d80a026d8dbd82ad)

## 実行

```bash
python3 ~/workspace/github.com/mikkegt/claude/skills/transcript-analyzer/analyze.py
```

オプション:

- `--project <name>` — 特定プロジェクトのみ集計（例: `lovelace`）
- `--days <N>` — 過去N日のセッションのみ集計（デフォルト: 全期間）
- `--top <N>` — 上位N件のみ表示（デフォルト: 全件）

## 出力

```
=== Tool Calls (1234 calls) ===
Name              Total    OK  Fail  Fail%
----------------------------------------
Bash               456   430    26     5%
Edit               320   315     5     1%
Read               280   278     2     0%

=== Skill Invocations (87 calls, 12 unique) ===
Name                       Total    OK  Fail  Fail%
read-article                 18    18     0     0%
review-pr                    12    11     1     8%
shinkoku:journal              9     7     2    22%
```

## 使い方

1. 月1回程度実行して傾向を見る
2. 失敗率の高いスキル/ツールを特定
3. 該当スキルのSKILL.mdやCLAUDE.mdのルールを改善
4. 次回の集計で改善効果を確認

## 制約

- transcriptは `cleanupPeriodDays` の期限（デフォルト30日）を過ぎると削除される
- 長期トレンドを見たい場合は定期的にスナップショットを保存する必要がある
