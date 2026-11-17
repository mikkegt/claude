# claude をホーム/ルートで起動しないガード（zsh / bash）

Claude Code を `~/` や `/` で起動すると、ホーム全体やファイルシステム全体が作業対象になり事故が起きやすい。特定のプロジェクトディレクトリに `cd` してから起動するように、シェル関数で強制する。

## スニペット

```zsh
claude() {
  if [ "$PWD" = "$HOME" ] || [ "$PWD" = "/" ]; then
    echo "refusing to run claude in $PWD — cd into a project dir first (use 'command claude' to override)." >&2
    return 1
  fi
  command claude "$@"
}
```

`~/.zshrc`（または `~/.bashrc`）に貼って、`source ~/.zshrc` で反映。

## Codex と Antigravity CLI にも同じガードを付ける

Codex（`codex`）と Antigravity CLI（`agy`）も、起動したディレクトリを作業対象にするので、同じ事故が起きる。関数名と `command` の後ろのコマンド名だけを替えて、同じ形で貼る（2026-11-17 に Mac の zsh で、`~` と `/` では断られ、プロジェクトのディレクトリでは起動できることを確かめた）。

```zsh
codex() {
  if [ "$PWD" = "$HOME" ] || [ "$PWD" = "/" ]; then
    echo "refusing to run codex in $PWD — cd into a project dir first (use 'command codex' to override)." >&2
    return 1
  fi
  command codex "$@"
}

agy() {
  if [ "$PWD" = "$HOME" ] || [ "$PWD" = "/" ]; then
    echo "refusing to run agy in $PWD — cd into a project dir first (use 'command agy' to override)." >&2
    return 1
  fi
  command agy "$@"
}
```

逃げ道も同じで、`command codex` / `command agy` と打てば関数を通らない。

## 何をしているか

- 関数名を `claude` にすることで、素の `claude` コマンドを覆う
- `$PWD` が `$HOME` または `/` なら、標準エラーに警告を出して `return 1` で終了
- それ以外のディレクトリなら `command claude "$@"` で本物のバイナリを呼ぶ
  - `command` は関数を無視して実体を呼ぶための組み込み。ここで再帰を防ぐ

## 逃げ道

- `command claude` と直接叩けばこの関数を通らず、`~/` でも起動できる（動作確認したい時など）

## モデルを固定したい場合

最終行を書き換えて `--model` を挿入する。例: Opus 4.7 に固定する:

```zsh
  command claude --model claude-opus-4-7 "$@"
```

引数で `--model` を後から渡せば上書きできる（後勝ち）。

## bash でも動く

zsh 固有構文は使っていないので、Ubuntu 等の `~/.bashrc` に同じ形で貼れる。
