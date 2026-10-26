---
name: mulmocast-movie-linux
description: Render a MulmoCast app project into a movie on a Linux machine (Ubuntu) with the mulmocast CLI, instead of pressing "コンテンツ生成" in the Mac app. Use when generation in the MulmoCast app makes the Mac very slow, when the user wants to render on a more powerful Linux box, or when puppeteer's Chrome on Ubuntu fails with "No usable sandbox!". Triggers: "Ubuntu で動画を作りたい", "Linux で書き出す", "MulmoCast が重い", "コンテンツ生成を別のマシンで".
---

# MulmoCast のプロジェクトを Linux で動画にする

MulmoCast のアプリで作ったプロジェクト（`script.json` と音声のフォルダ）を、Linux 上のコマンドライン版 mulmocast で動画にする。台本やスライドを直すのはアプリ、動画の書き出しだけを Linux で行う。

## 先に知っておくこと（2026-10-26 に試して分かった）

- アプリ（1.0.14）は Mac 用しか配布されていない。リリースにダウンロード用のファイルが無く、README も Mac のビルドしか案内していない。Linux ではコマンドライン版を使う
- 書き出しで時間がかかるのは、Chrome で HTML を絵にする処理（スライド、字幕）と、ffmpeg で動画に仕上げる処理。mulmocast は絵を 1 枚描くたびに Chrome を起動して閉じる。CPU とメモリが多いマシンほど速い
- 試したのは、全ビートにアップロードした音声があり、スライドが `html_tailwind` の台本だけ。全ビートに音声があってスライドが HTML なら API を呼ばないので、Linux に API キーを置かなくてよい。音声や画像を生成するビートがある台本は試していない

測った例: Ubuntu 26.04、CPU 32 個、メモリ 121 GB のマシンで、13 ビート・7 分 20 秒の台本が 32 秒で動画になった（うち ffmpeg が 20 秒）。同じ台本を Mac のアプリで作った時間は測っていない。

## 用意するもの（Linux 側）

- Node.js 22 以上（mulmocast 2.6.15 の `package.json` の `engines` が `>=22.0.0`）
- `ffmpeg` と `ffprobe`。`PATH` にあれば使われる。mulmocast 2.23.0 が使う `@modernized/fluent-ffmpeg` は、環境変数 `FFMPEG_PATH` と `FFPROBE_PATH` も読む（2.6.15 で同じかは確かめていない）
- システムに入った Google Chrome（`/usr/bin/google-chrome`）。理由は「Chrome のサンドボックス」の節
- 日本語のフォント（`fc-list :lang=ja | wc -l` が 0 でないこと）

他人と共有しているマシンでは、sudo を使わず、自分のホームの中だけで作業する。

## 手順

1. アプリが中で使っている mulmocast の版を Mac で調べる。版をそろえると、アプリと同じ処理で動画ができる

       grep -aoE '"mulmocast": ?"[^"]+"' /Applications/MulmoCast.app/Contents/Resources/app.asar

2. Linux のホームに作業用フォルダを作り、同じ版を入れる。`-g` で入れない

       mkdir -p ~/mulmocast-render && cd ~/mulmocast-render && npm init -y && PUPPETEER_SKIP_DOWNLOAD=true npm install mulmocast@<版>

   `PUPPETEER_SKIP_DOWNLOAD=true` は、使わない Chrome（約 650 MB）のダウンロードを止めるため。2026-10-26 は付けずに入れて、ダウンロードされた Chrome を後から消した。付けて入れる手順はまだ試していない

3. アプリを終了してから、プロジェクトのフォルダを丸ごとコピーする。`script.json` の音声と BGM は `./upload_audio/...` のような相対パスで書かれているので、フォルダの形を変えない

       rsync -a "$HOME/Library/Application Support/MulmoCast/projects/<プロジェクトのフォルダ>" <Linux のホスト>:mulmocast-render/

4. プロジェクトのフォルダの中で書き出す。出力先はアプリの `output/` と分ける

       cd ~/mulmocast-render/<プロジェクトのフォルダ> && PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome npx --prefix ~/mulmocast-render mulmo movie script.json -o out-linux -f

   最後に `Video created successfully!` と出れば完成。動画は `out-linux/script_<lang>__<lang>.mp4`（日本語なら `script_ja__ja.mp4`）

5. 動画を Mac に持ってきて確かめる

       rsync -a <Linux のホスト>:mulmocast-render/<プロジェクトのフォルダ>/out-linux/script_ja__ja.mp4 ~/Downloads/

台本を直したら、手順 3 からやり直す。

## Chrome のサンドボックス（Ubuntu 23.10 以降）

puppeteer がダウンロードした Chrome は、起動したところで次のように止まる。

    FATAL:content/browser/zygote_host/zygote_host_impl_linux.cc:130] No usable sandbox! If you are running on Ubuntu 23.10+ ...

Ubuntu 23.10 以降は、AppArmor が一般ユーザーにサンドボックス用の user namespace を作らせないため。システムに入った Google Chrome は、root の setuid が付いた補助プログラム（`/opt/google/chrome/chrome-sandbox`）でサンドボックスを作るので、制限を受けない。mulmocast 2.6.15 は `puppeteer.launch` に `executablePath` を渡していないので、環境変数 `PUPPETEER_EXECUTABLE_PATH` で Chrome を差し替えられる。

- NEVER `--no-sandbox` で回避しない。スライドの HTML は外部の CDN からスクリプトを読み込むので、サンドボックスを外さない
- NEVER AppArmor の設定を変えない。sudo が要り、マシン全体のセキュリティに影響する

## まだ確かめていないこと

- 字幕の書体: Linux では Noto 系の書体で描かれた。Mac のアプリで作った字幕と、書体や折り返しの位置が同じかは比べていない
- アプリで作った動画と、全体が同じになるか（音量、字幕のタイミング）
