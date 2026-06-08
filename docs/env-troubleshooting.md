# 環境トラブル調査メモ

たまにしか踏まないが踏むと忘れている系のメモ。症状で引けるよう見出しを切る。

## JetBrains 全般（CLion / GoLand / PyCharm / WebStorm）

### フォーマッターが効かない / ショートカットが反応しない

チェック順:

1. `⇧⌘A` → `Reformat Code` で動くか
   - 動く → ショートカット問題（macOS のキーボードショートカットや他アプリと衝突、Settings → Keymap → `Reformat Code` で割り当て確認）
   - 動かない → 次へ
2. ステータスバーや右下に「準備中」「インデックス中」が出ていないか → 出ていれば待つ
3. それでも動かない → IDE 個別の節へ

### 警告ダイアログを安易に閉じない

「ビルドシステムが見つかりません」「CMake プロジェクトとして読み込みますか」などの警告は無視せず読む。これらを消し続けていると、言語サーバーが起動せず、補完やフォーマットがうまく動かなくなる。

---

## CLion (C/C++) 固有

### `⌥⌘L` が「アクション準備中」のまま固まる

原因: clangd が起動していない。

確認: View → Tool Windows → clangd がグレーアウトしていたら未起動。

対処:

- ルートに最小 `CMakeLists.txt` を置く
- git に含めたくない場合は `.git/info/exclude` に追記して個人だけで除外する（`.gitignore` はチームに共有されるので NG）
- File → Reload CMake Project、または `CMakeLists.txt` を右クリック → Load CMake Project

最小 `CMakeLists.txt` の例（C++98、IDE 用のみ。実ビルドは Makefile）:

```cmake
cmake_minimum_required(VERSION 3.10)
project(myproj CXX)

set(CMAKE_CXX_STANDARD 98)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

file(GLOB_RECURSE SOURCES CONFIGURE_DEPENDS "src/*.cpp" "src/*.hpp")
add_executable(myproj_ide_only ${SOURCES})
```

### `.clang-format` の場所と確認方法

プロジェクトルートに置く。Settings → Editor → Code Style → C/C++ で「設定は ClangFormat に上書きされる可能性があります」と出ていれば認識されている。

### `.clang-format` が認識されない場合

Settings → Editor → Code Style → C/C++ の **整形エンジン** が「CLion フォーマッター」になっていると、`.clang-format` の一部設定しか流用されず、アクセス識別子インデント等が期待通りにならない。

対処:

1. 整形エンジンを「**ClangFormat**」のラジオボタンに切り替える
2. 「組み込みの clang-format ではなく外部の clang-format を使用する」は **チェックを外す**（バンドルで十分）。なお、このパス欄は clang-format **実行ファイル** を指定する場所で、`.clang-format` 設定ファイル自体を指定しても動かない
3. Apply 後、エディタ上の既存コードは自動再整形されないので **⌥⌘L (Reformat Code)** で手動整形する

---

## GoLand (Go) 固有

- `gofmt` 自体は go.mod が無くても動く（単一ファイルの整形）
- 補完・ジャンプ・lint 等の `gopls` 機能は go.mod が必要
- フォーマットが効かない場合は Settings → Tools → File Watchers で `goimports` / `gofmt` の有効化を確認

（→ ハマったら追記）

---

## PyCharm (Python) 固有

- 標準は IDE 内蔵フォーマッター
- Black / Ruff を使うなら File Watchers か外部ツールとして登録
- Settings → Tools → External Tools / File Watchers

（→ ハマったら追記）

---

## WebStorm (JS/TS) 固有

- Settings → Languages & Frameworks → JavaScript → Prettier
- "On 'Reformat Code' action" にチェック
- Prettier が `node_modules` に入っているか、または globally install 済みか確認

（→ ハマったら追記）

---

## Mac 環境

### Homebrew が `Cannot install under Rosetta 2` で失敗する

症状:

```
Error: Cannot install under Rosetta 2 in ARM default prefix (/opt/homebrew)!
To rerun under ARM use:
    arch -arm64 brew install ...
```

原因: ターミナルが Rosetta（x86_64）で動いている。

確認:

```sh
arch          # i386 → Rosetta、arm64 → ネイティブ
uname -m      # 同上
```

対処:

1. ターミナル.app を Finder で選択 → ⌘I → 「Rosetta を使用して開く」のチェックを外す
2. ⌘Q で完全終了 → 起動し直し（ウィンドウを閉じるだけでは反映されない）
3. `arch` で `arm64` を確認

一発だけ arm64 で実行したいとき:

```sh
arch -arm64 brew install <formula>
```

### 今のターミナルが何か特定したい

```sh
ps -p $PPID -o comm=
```

親プロセス名が出る。複数のターミナル（純正 Terminal / iTerm / Ghostty / IDE 付属）を使い分けていて、どれが Rosetta で動いているか分からないときに使う。

### Homebrew のインストール先

- Apple Silicon ネイティブ: `/opt/homebrew`
- Intel / Rosetta: `/usr/local`

両方混在していると `which brew` で判別できる。`.zprofile` に `eval "$(/opt/homebrew/bin/brew shellenv)"` を入れておくと PATH が安定する。
