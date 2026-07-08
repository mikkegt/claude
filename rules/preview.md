# ローカルプレビュー（スクショ目視確認）

フロント案件で開発サーバーの画面を Claude 自身が目視確認したいときに使う。ヘッドレス
Chrome でスクショを撮り Read で開く。実行ファイルのパスは直書きする（変数に入れると
静的解析を壊して許可待ちになる。rules/bash-permission.md 参照）。

## macOS

    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
      --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
      --window-size=900,1300 --screenshot=/tmp/shot.png <URL>

## Ubuntu / Linux

    /usr/bin/google-chrome \
      --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
      --window-size=900,1300 --screenshot=/tmp/shot.png <URL>

Chromium を使っている場合は `/usr/bin/chromium` に読み替える。

## 共通

- 解像度・ウィンドウサイズは案件に合わせて調整する例値。
- MUST 常駐サーバー（npm run dev / hugo server 等）はフォアグラウンドで起動しない。
  Bash ツールの run_in_background で起動し、撮影後に確認する
  （フォアグラウンドだと制御が返らず固まるため）。
