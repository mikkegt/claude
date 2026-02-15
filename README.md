# claude

Claude Code のグローバル設定、プロジェクト別テンプレート、Skillを管理するリポジトリ。

## セットアップ

### グローバル CLAUDE.md

`~/.claude/CLAUDE.md` にシンボリックリンクを貼る:

```bash
ln -s /path/to/this/repo/CLAUDE.md ~/.claude/CLAUDE.md
```

### グローバル settings.json

`~/.claude/settings.json` はマシン固有データ（タイムスタンプ等）を含むため、シンボリックリンクではなく手動で管理する。このリポジトリの `settings.json` はバックアップ・リファレンス用。

新しいマシンをセットアップする際:
```bash
cp /path/to/this/repo/settings.json ~/.claude/settings.json
```

### プロジェクト別テンプレート

プロジェクトの CLAUDE.md にテンプレートへのシンボリックリンクを貼る:

```bash
ln -s /path/to/this/repo/templates/python.md /path/to/project/CLAUDE.md
```

プロジェクト固有のルールが必要な場合は、シンボリックリンクではなく実ファイルとして作成する。

## ファイル構成

```
CLAUDE.md       - グローバル設定（~/.claude/CLAUDE.md にシンボリックリンク）
settings.json   - グローバル設定のバックアップ（手動コピー用）
templates/      - プロジェクト別テンプレート（今後追加）
skills/         - 汎用Skill（今後追加）
```

## 読み込み順序

1. `~/.claude/CLAUDE.md`（グローバル）
2. プロジェクトの `CLAUDE.md`（プロジェクト固有）

両方読み込まれるため、プロジェクト側でグローバルの設定を上書きできる。

## 注意事項

- Git操作のルールは GitHub / GitLab 両対応（PR/MR 表記）
- グローバルでは「フィーチャーブランチを切る」がデフォルト。個人プロジェクトでは CLAUDE.md で緩和可能
