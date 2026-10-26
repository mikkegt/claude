---
name: gemini-designed-voice-tts
description: Speak text with a voice the user designed in Google AI Studio (Gemini TTS, e.g. a voice named "Coral Reef Guide 3"), one WAV per beat, for MulmoCast or any video. Use when the user wants audio in "the voice I made in AI Studio", pastes AI Studio's "Get code" TTS snippet that fails with "No matching speaker voice found", or asks to make narration audio for MulmoCast beats with a Gemini voice that MulmoCast's own TTS settings cannot select. Triggers: "スタジオで作った声", "AI Studio の声で", "Gemini TTS の新しい声", "ビートの音声を作って".
---

# AI Studio で作った声で読み上げる

Google AI Studio の voice design で作った声（表示名は「Coral Reef Guide 3」のような名前）で、文を WAV にする。スクリプトは同じフォルダの `tts.py`。

## 先に知っておくこと（2026-10-24 に試して分かった）

- 作った声は、API では表示名ではなく `voice_` で始まる ID で指定する。表示名を渡すと 400 `No matching speaker voice found for name: ... and language: ` が返る
- 作った声は Interactions API（`client.interactions.create`）でだけ使えた。AI Studio の「Get code」が出すコードは `generateContent` を使っていて、表示名でも ID でも同じ 400 になった。`language_code` を足しても、API の版を `v1alpha` にしても変わらなかった
- 同じキー・同じモデル（`gemini-3.8-flash-tts`）でも、用意された声（`Kore` など）なら `generateContent` で音声が返った。キーの問題ではない
- ID は `client.voices.list()` で一覧できる。作った声はプロジェクトに保存され、有効期限は約 1 年で、使うたびに延びる（Gemini API のドキュメント speech-generation のページ）
- 言語は自動で判定される（ドキュメント）。日本語の文の中の英字（Docker、namespace、`uname -r`、`ps aux` などを含む 9 ビート）は、ユーザーが 6 ビートほど聞いて、ちゃんと発音できていたと言った。どのビートを聞いたかは記録していない

## 準備

仮想環境は公開リポジトリの外に置く。無ければ作る。

    python3 -m venv ~/.local/share/gemini-tts-venv
    ~/.local/share/gemini-tts-venv/bin/pip install -q google-genai

2026-10-24 に `google-genai` 2.33.0 で動いた。

API キー:

- 環境変数 `GEMINI_API_KEY` があれば、環境変数のキーを使う
- 無ければ MulmoCast の `~/Library/Application Support/MulmoCast/settings.json` の `APIKEY.GEMINI_API_KEY` を読む
- NEVER キーの値を画面・会話・ファイルに出さない。`settings.json` を `cat` や `jq .` で表示しない。項目があるかは `jq '.APIKEY.GEMINI_API_KEY | type == "string" and startswith("AIza")'` のように真偽だけで確かめる
- API の利用料がかかる。何度も作り直す前にユーザーに伝える

## 手順

以下、`TTS` は `~/.local/share/gemini-tts-venv/bin/python -I <skill のフォルダ>/tts.py` を指す。

1. 声の ID を調べる。表示名と ID の対応が出るので、ユーザーが言った表示名の ID を使う

       TTS voices

2. ユーザーが AI Studio で使った style（「Get code」のコードの `style=` の文字列）を聞く。無くてもよい。作った声は人物像が声に入っているので、style は短くする（ドキュメントの推奨）
3. まず 1 文だけ作って、ユーザーに聞いてもらう（`open <ファイル>` で再生できる）

       TTS speak --voice voice_xxx --style "Style: ..." --out <出力先> --text "読ませる文"

4. よければ、ビートのセリフを JSON の配列（1 要素 1 ビート）に書き出して、まとめて作る。番号を付けると、番号のビートだけ作る。出力は `<出力先>/beat-NN.wav`。同じ名前のファイルがあれば上書きせずに止まる

       TTS speak --voice voice_xxx --style "Style: ..." --out <出力先> --texts beats.json
       TTS speak --voice voice_xxx --style "Style: ..." --out <出力先> --texts beats.json 3 7

5. `afinfo <ファイル>`（macOS）で長さを確かめて、一覧にして伝える

## 速さと語尾を調整する

API には速さを数値で指定する項目が無い（2026-10-24 に `google-genai` 2.33.0 の Interactions API の型で確かめた。`speech_config` は `voice`・`language`・`speaker` だけ）。語尾は style の文で、速さは ffmpeg で調整する。

- 語尾: style に一言足す。強い言い方にすると、言い方どおりに強く出すぎる。2026-10-24 にユーザーと試した結果:
  - 「ほんの少しだけテンポよく話し、語尾は曖昧にせずはっきり言い切る。」: 語尾がキレすぎた
  - 「語尾を伸ばさず、自然に軽く終える。」: ちょうどよかった。速さも頼んでいないのに、元の style より約 13% 短くなった（32.24 秒 → 27.96 秒）
- 速さ: ffmpeg の `atempo` で少し速くする。声の高さは変わらない。`1.05` で 5% 速くなる。`tts.py speak` に `--atempo 1.05` を付けると、作るときに続けてかける。できている WAV にかけるときは ffmpeg を直接使う（`-n` で既にあるファイルを上書きしない）

      TTS speak --voice voice_xxx --style "Style: ..." --atempo 1.05 --out <出力先> --texts beats.json
      ffmpeg -loglevel error -n -i beat-02.wav -filter:a atempo=1.05 beat-02-fast.wav

- 2026-10-24 にユーザーが選んだのは、「語尾を伸ばさず、自然に軽く終える。」の style で作り、`atempo=1.05` をかけた版だった。atempo だけでは語尾の伸びは残った
- ところが 2026-10-25 に動画を通して聞き直したユーザーが、「語尾を伸ばさず、自然に軽く終える。」でも毎回はっきり言い切りすぎて気になると言った。1 ビートで比べたときは分からず、続けて聞くと気になった。ビート 2 で 3 つ比べて、「語尾は柔らかく、自然に終える。」に決まった（ほかの 2 つは「語尾に少し余韻を残す。」「語りかけるように話す。」）。語尾は、1 ビートで決めた後に、何ビートか続けて聞いてもらってから全部を作る
- 調整は、長めのビート（30 秒くらい）で比べる。短い 1 文では差が聞き取りにくく、長さもほとんど変わらなかった
- 作るたびに読み方が少し変わる（temperature の既定値のまま）。1 回ずつの比較で決めつけない
- AI Studio の画面にも微調整の操作があるが、API のどの項目に対応するかは確かめていない。画面で調整したら「Get code」のコードを貼ってもらい、変わった箇所を読む

## 用意された日本語の声の候補

作った声のほかに、Google が用意した声も `--voice` に ID を渡して同じように使える。`client.voices.list()` には `ja-jp-` で始まる日本語の声が 120 個あった（2026-10-25）。どの声にも英語の説明（年齢、職業、話す地域、声の性質）が `display_name` と一緒に付いていて、性別は書かれていない。`tts.py voices` は作った声だけを出すので、用意された声は `voices.list()` を直接呼んで探す。

2026-10-25 に、技術解説の動画のナレーションとして、東京の日本語の声から 5 つを選んで比べた。style は「Style: 語尾は柔らかく、自然に終える。」だけにして、`atempo 1.05` をかけた。用意された声には人物像があるので、年齢や性別を style に書かなかった。ユーザーは 5 つともよいと言い、ほかのプロジェクトでも候補にしたいと言った。

| ID | 一覧の説明（訳） |
|---|---|
| `ja-jp-podcaster-2` | 28 歳のインタビュアー。ラジオで、自信があってはっきりしている。技術解説の動画にユーザーが選んだ |
| `ja-jp-techagent-7` | 32 歳のテックサポート。はっきりした中くらいの高さの声で、親しみやすい |
| `ja-jp-tutor-4` | 24 歳の教授。ポッドキャストで、きちんとしているけれど話しかけやすい |
| `ja-jp-advisor-8` | 39 歳の弁護士。はっきりした中くらいの高さの声で、親しみやすい |
| `ja-jp-tutor-9` | 40 歳の司書。ラジオで、自信があってはっきりしている |

AI Studio でささやくような声として作った声は、解説の動画には合わないとユーザーが言った。声は用途に合わせて選ぶ。解説なら、まず上の候補から聞いてもらう。

## MulmoCast で使うとき

mulmocast 2.23.0 のソースで確かめた（2026-10-24）。アプリ側の版は別なので、最初は 1 ビートで試してもらう。

- ビートに音声をアップロードすると、音声のあるビートは TTS を使わない（`lib/actions/audio.js` の `preprocessorAgent`、`needsTTS = !beat.audio && ...`）
- 字幕は、音声があってもビートの `text` から作られる（`lib/actions/captions.js` の `generateBeatCaptions`）。字幕分割（`captionSplit: "estimate"`）は、ビートの長さ（＝アップロードした音声の長さ）を文の文字数の比で割り振る（`calculateTimingRatios`）。音声の中身は見ない。音声に合わせる設定は無く、`captionSplit` は `none` と `estimate` だけ
- だから、音声に読ませる文とビートの `text` を同じにする。アプリでセリフを直したら、直したビートの音声も作り直してアップロードし直す
- WAV を拒む処理はソースに無かった。アプリのアップロード画面が WAV を受け付けなければ、`ffmpeg -i beat-01.wav beat-01.mp3` で変換する
- `script.json` を直接書き換えるときは、アプリを終了してから行う。開いたままだと、アプリがメモリ上の古い内容で上書きする

### 字幕のタイミングを音声に合わせる

文字数と読む時間は比例しないので、字幕がずれる。英字（`Docker` は 6 文字でも日本語の 2〜3 文字ぶんの時間で読まれる）、段落の間、読点の間でずれる。2026-10-24〜25 に測った例では、日本語のビートで最大 3.3 秒早く、英語のビートで最大 1.6 秒早く・約 1 秒遅く出ていた。

直し方: whisper で文ごとの話し始めを測り、ビートの `texts`（字幕の文の配列。あると `text` を区切り文字で分ける処理より優先される）の各文の後ろに幅ゼロの空白（U+200B）を足して、文字数の比を時間の比に合わせる。計算は同じフォルダの `align.py` が行う。2026-10-25 に日本語 9 ビートと英語 9 ビートで使った。U+200B が字幕の見た目に影響しないかは、ユーザーにまだ確かめてもらっていない（2026-10-26 時点）。

1. ビートの音声を 16 kHz モノラルにして、whisper.cpp でトークンごとの時刻付きの JSON を作る

       ffmpeg -loglevel error -i beat-03.wav -ar 16000 -ac 1 beat-03-16k.wav
       whisper-cli -m <ggml-large-v3-turbo.bin> -l ja -ojf -of beat-03 -f beat-03-16k.wav

2. ビートの長さを出す。MulmoCast のビートの長さは、音声の長さ＋`audioParams.padding`（最後のビートだけ `closingPadding`）だった（`output/script_studio.json` の `beats[].duration` と比べて確かめた）
3. `align.py` で `texts` を作る。表示開始の今と直した後、話し始めの表が標準エラーに出る。文と文の間の真ん中で切り替えるので、字幕は話し始めより少し前に出る

       python3 -I align.py beat-03.json script.json <ビート番号（0 始まり）> <ビートの長さ> > beat-03-texts.json

4. アプリを閉じて、`jq --slurpfile t beat-03-texts.json '.beats[2].texts = $t[0]'` のように `script.json` に入れる。空白と U+200B を除いた `texts` の連結が `text` と同じかを確かめる

気をつけること:
- アプリでセリフ（`text`）を直すと、`texts` と食い違う。字幕は `texts` のほうが出る。セリフを直したら、音声と `texts` を作り直す。タイミング合わせは、セリフと音声が確定してから最後に行う
- 音声を作り直したら、`texts` も作り直す
- whisper.cpp を Homebrew の外でビルドしていると、Homebrew の `libomp` に頼っているのに、`brew autoremove` が使われていないと判断して消すことがある（2026-10 に起きた）。`Library not loaded: .../libomp.dylib` が出たら `brew install libomp` で入れ直す

### 声が小さいとき

BGM があると、mulmocast は声と BGM を ffmpeg の `amix` で混ぜる。何も指定しないと `amix` は 2 つの音をそれぞれ半分にするので、声が約 6 dB 小さくなる（`lib/agents/add_bgm_agent.js`）。2026-10-24 に測った例では、アップロードした声が -18.8 LUFS、できた動画が -26.2 LUFS だった。

`audioParams` に `ttsVolume`（0〜2）を書くと、半分にしない混ぜ方（`normalize=0`）とリミッターに変わる。BGM も半分にされなくなるので、BGM を今と同じ大きさにするなら `bgmVolume` を半分にする。2026-10-25 にユーザーが選んだのは `ttsVolume: 1`、`bgmVolume: 0.14`（元は 0.2）で、声は +6 dB、BGM は +3 dB になった。MulmoCast アプリ 1.0.14 の中にも同じ処理があることを確かめた
