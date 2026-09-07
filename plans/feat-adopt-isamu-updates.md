# isamu/claude の 2026-07〜08 更新の取り込み

日付: 2026-09-07

## 背景

mikkegt/claude は isamu/claude を元に作られたが、git 履歴は繋がっていない（merge-base なし）ため cherry-pick はできず、内容の移植になる。upstream では 2026-07-02 から 2026-08-21 にかけて 15 コミットが入り、CLAUDE.md からリファレンス資料を docs/ へ分割する構成変更と、実案件で踏んだ失敗を書き起こした大型の skill / docs 追加が行われた。mikkegt 側には 7 月初旬までの成果しか入っておらず、加えて pr-babysit / dep-upgrade-safe / pr-merge-tidy の 3 スキルが、存在しない gh-review-loop を参照したままリンク切れになっていた。

ユーザーの依頼は「upstream の直近 2〜3 ヶ月を読んで更新状況を把握し、取り込めそうなものをリストアップ」→ 提示したリストのうち優先度 高 と 中 を実施、という 2 段階。

## 取り込んだもの

優先度 高:

- `skills/gh-review-loop/SKILL.md`: GitHub 側のレビューボットが投稿したコメントを読んで fix-push を回すループ。イテレーション上限なし、PR 上の台帳コメントで決着済み指摘の再燃を防ぐ、5 ラウンドごとに PR 全体を読み直す、「マージではなくクローズ」も終了条件、という 8 月の更新を含む版。リンク切れだった 3 スキルの参照が実在化する
- `rules/debugging.md`（新規・日本語）: upstream `docs/debugging-methodology.md` の移植に、open PR #37 の「他人の報告は症状だけ見て自分で調べ、後で答え合わせする」を加えたもの。報告が本物か（再現するか / 到達可能か / そもそも間違った挙動か）を修正の設計前に確定する手順が中心
- `skills/refactor-safely/SKILL.md`: 「挙動は変わらない」が主張の全部である変更を、旧コードと新コードを並べて走らせて検証する手順。ハーネス自体が壊れていて 0 件と出る失敗パターンまで含む

優先度 中:

- `rules/workflow-common.md` に「Issue を立てる前に」節を追加（upstream `docs/issue-filing.md` の日本語化）。重複チェック、入力の producer を grep、到達可能性を示せないなら issue にしない、部分対応の PR に closing keyword を書かない
- `rules/coding.md` に追加: 上限の分からないファイルを丸読みしない（upstream `docs/large-file-reading.md`）、テスト設計（判断と I/O の分離、DI、壊して赤くなるかの確認、呼び出し元も壊す）
- `skills/parallel-tranches/SKILL.md`: 1 つのバックログ issue を複数エージェントの worktree で並列に潰すときの調整ルールと失敗集。upstream では CLAUDE.md のルール節と docs/ の事例に分かれていたものを、1 つの skill に統合した
- `skills/codex-local-review/SKILL.md`: PR にする前のローカル diff を codex に読み取り専用でレビューさせる

## 移植時の適応

- 固有名詞の一般化: mikkegt/claude は public リポジトリなので、`rules/privacy.md` に従い他案件のリポジトリ名と issue 番号を落とし、計測結果の記述だけ残した
- 存在しないスキルへの参照を差し替え: `/pr-ui-test` → 手動クリックスルー + `rules/preview.md`、`pr-quality-sweep` → `pr-merge-tidy` / `pr-babysit`
- マージ方式の記述を緩めた: upstream の「NEVER squash」はプロジェクト固有の慣習で、mikkegt の `rules/git-common.md` は方式を規定していないため「リポジトリの慣習に従い、squash 前にユーザーへ確認」に変更
- 言語: skills/ は既存に合わせて英語、rules/ は既存に合わせて日本語
- 分量の置き場所: 常時読み込まれる rules/ には要約とポインタだけを置き、大きいリファレンス（refactor-safely 49KB、gh-review-loop 25KB、parallel-tranches 20KB）は必要時のみ読まれる skills/ に置いた

## 取り込まなかったもの

- upstream の CLAUDE.md 本体: yarn / TypeScript / Vue / Tailwind 前提のスタック固有ルールが本文に埋まっており、mikkegt の言語非依存な CLAUDE.md + rules/ 構成と前提が違う
- `skills/codex-cross-review` の 72KB 版: mikkegt には 10KB 版がある。ラウンド数削減のための PR ティア分けなど運用密度が高く、必要な節だけ抜くほうが実用的と判断。次回以降の検討事項
- `docs/cross-platform-ci.md` / `docs/windows-gotchas.md`: Windows 上で Node を動かす案件がない
- `docs/web-debugging.md`: Playwright MCP 前提で、mikkegt の `rules/preview.md`（ヘッドレス Chrome）と手段が噛み合わない
- `skills/pr-ui-test` / `discord-release` / `init-project` / `pr-quality-sweep`: 特定プロダクト・特定スタック前提、または `pr-babysit` と守備範囲が重なる
- open PR #37 の 3 点目（方針が決まった修正は確認なしで commit / push / PR / マージまで進む）: mikkegt の `rules/git-mac.md`（コミット・プッシュはユーザーの明示的な許可が必要）と正面から衝突するため見送り。1 点目（症状から先に調べる）と 2 点目（指摘の却下も適用と同じ検証を要求する）は `rules/debugging.md` に取り込んだ

## 未実施

- upstream の CLAUDE.md は `docs/pr-contract.md` を参照しているがファイルが存在しない（リンク切れ）。mikkegt 側には持ち込んでいないので影響なし
- 移植したルールを実際の作業で使った検証はしていない。文章の移植のみ
