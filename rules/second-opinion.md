# 別のモデルに意見を聞く（Gemini と Codex）

グローバル CLAUDE.md の「設計判断を多角的に見たいときは、別のモデルに同じ問いを投げて突き合わせる」の具体化。Mac では、Claude のサブエージェント（Sonnet / Fable）のほかに、Gemini と Codex を CLI から呼べる（2026-11-17 に Mac で確かめた）。

## 呼び方

Gemini は Antigravity CLI（`agy`、Homebrew の cask `antigravity-cli`）で呼ぶ。Homebrew の formula `gemini-cli` は上流のサポートが終わり、2026-12-18 に無効になるので使わない。

    agy -p "<問い>" --model gemini-3.8-flash-high --mode plan --settings <agy-readonly.json の絶対パス> --print-timeout 300s

- `-p` は一度だけ問いを投げて答えを表示する。`--mode plan` でファイルを書き換えさせない
- `-p` ではツールの許可を聞けないので、ファイルを読ませるときは `--settings` で許可を渡す。許可のファイルは、`~/.claude/rules` のリンク先リポジトリにある `snippets/agy-readonly.json` で、読む・一覧する・検索するだけを許可する。絶対パスは `readlink ~/.claude/rules` で引いたリンク先の、`rules` を `snippets/agy-readonly.json` に置き換えて作る。`--settings` に JSON を直接書くと、Bash の静的解析が承認待ちにするので、ファイルで渡す
- 使えるモデルは `agy models` で見る。2026-11-17 の時点で Gemini は `gemini-3.8-flash-{high,medium,low}` だけだった。一覧にある Claude のモデルは、Claude と独立した視点にならないので使わない
- サインインはユーザーが `agy` を引数なしで起動して行う。サインインしていないと `agy models` がエラーになる

Codex は `codex exec` で呼ぶ。

    codex exec --sandbox read-only --skip-git-repo-check -o <答えの出力ファイル> "<問い>"

- `--sandbox read-only` でファイルを書き換えさせない。答えは `-o` のファイルに出る

## 進め方

- MUST 3 つのモデル（Claude のサブエージェント、Gemini、Codex）に同じ問いを渡す。問いは 1 つのファイルに書き（前提、問い、字数、答えの形）、各モデルには問いのファイルを読ませる。条件が揃うので答えを並べて比べられる
- MUST 問いのファイルに、ユーザーの個人情報、API キー、非公開の固有名詞を入れない。Gemini と Codex は外部のサービスに送られる
- SHOULD 時間がかかるので `run_in_background` で並べて走らせる
- MUST 答えは並べてユーザーに見せ、一致した点・割れた点・各モデルだけが指摘した点を分けて書く。どのモデルの主張も、一次情報で確かめるまでは未確認として扱う
