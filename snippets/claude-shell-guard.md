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
