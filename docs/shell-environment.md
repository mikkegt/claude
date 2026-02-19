# Claude Code とシェル環境

Claude Code はターミナル上で動作する CLI ツールだが、シェルの設定ファイルの読み込み方に注意が必要。

## 問題: `.zshrc` に書いた PATH が Claude Code から見えない

pip や Homebrew でインストールした CLI ツール（`gcalcli` など）を `.zshrc` で PATH に追加していても、Claude Code の Bash ツールから `command not found` になることがある。

### 前提: interactive シェルと non-interactive シェル

- **interactive シェル** -- 人間がキーボードで操作するシェル。ターミナルを開いたときに起動する。プロンプト表示、Tab 補完、oh-my-zsh のテーマ適用などはすべてこのモードの機能。
- **non-interactive シェル** -- スクリプトやツールが裏で実行するシェル。人間の入力を待たない。Claude Code の Bash ツールはこちら。

### 原因: `.zshrc` は interactive シェルでしか読まれない

zsh の設定ファイルと読み込み条件:

| ファイル | 読み込み条件 | interactive + login | non-interactive + login (`zsh -lc`) | non-interactive |
|----------|-------------|:---:|:---:|:---:|
| `.zshenv` | **常に** | o | o | o |
| `.zprofile` | login | o | o | x |
| `.zshrc` | **interactive** | o | x | x |
| `.zlogin` | login | o | o | x |

Claude Code の Bash ツールは non-interactive シェルとしてコマンドを実行する。`.zshrc` は interactive シェル専用の設定ファイルなので、読み込まれない。

### なぜ起動方法で挙動が変わるのか

| 起動方法 | `.zshrc` の PATH | `.zshenv` の PATH |
|----------|:---:|:---:|
| ターミナル（Ghostty等）から `claude` | 見える (*) | 見える |
| ランチャー（Raycast等）のスクリプト経由 | 見えない | 見える |
| CI/CD, cron 等 | 見えない | 見える |

(*) ターミナルエミュレータは interactive login shell を起動し、`.zshrc` を読む。Claude Code はその環境を継承する。Claude Code 自身が `.zshrc` を読んでいるわけではない。

#### `zsh -lc` の罠

ランチャーのスクリプトで `/bin/zsh -lc "claude"` と書いても `.zshrc` の PATH は通らない。

- `-l` = login shell にする
- `-c` = コマンドを渡して実行する（non-interactive になる）

login かどうかは関係ない。`.zshrc` が読まれるかどうかは **interactive かどうか** で決まる。

```
【ターミナル経由】
Ghostty → zsh (login + interactive) → .zshenv + .zshrc → claude

【ランチャー経由】
Raycast → zsh -lc (login + non-interactive) → .zshenv のみ → claude
```

### 解決策: `.zshenv` に PATH を書く

`.zshenv` は全ての zsh プロセスで読み込まれるため、ここに PATH を書くのが確実。起動方法に依存しない唯一の方法。

```bash
# ~/.zshenv
export PATH="/Library/Frameworks/Python.framework/Versions/3.13/bin:$PATH"
```

### `.zshenv` に書くべきもの・書くべきでないもの

**書くべきもの:**
- `export PATH=...` -- CLI ツールへのパス
- `export EDITOR=...` -- 環境変数

**書くべきでないもの:**
- エイリアス (`alias`)
- コマンド補完 (`compinit`)
- oh-my-zsh や starship などのシェルカスタマイズ

これらは interactive シェルでのみ意味を持つ設定なので `.zshrc` に書く。`.zshenv` に入れると、non-interactive シェル（スクリプト実行時など）でも不要な初期化が走り、予期しない動作を引き起こす。

## 参考: Claude Code の設定ファイル

| ファイル | 場所 | 用途 |
|----------|------|------|
| `CLAUDE.md` | `~/.claude/CLAUDE.md` | グローバル指示（全プロジェクト共通） |
| `CLAUDE.md` | プロジェクトルート | プロジェクト固有の指示 |
| `settings.json` | `~/.claude/settings.json` | パーミッション、許可コマンド等 |
| `MEMORY.md` | `~/.claude/projects/<project>/memory/` | プロジェクト別の学習メモ（自動生成） |

`CLAUDE.md` はシンボリックリンクで Git リポジトリから管理すると、バージョン管理・複数マシン間の同期が楽になる。
