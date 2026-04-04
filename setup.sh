#!/bin/bash
# Claude Code プロジェクトセットアップスクリプト
#
# 使い方:
#   setup.sh personal   - 個人プロジェクト用（CLAUDE.md + .claude/rules/ をシンボリックリンク）
#   setup.sh team       - チームプロジェクト用（CLAUDE.local.md + .claude/rules/ をコピー、.gitignore に追記）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(pwd)"

usage() {
  echo "Usage: $0 {personal|team}"
  echo ""
  echo "  personal  個人プロジェクト用セットアップ"
  echo "            - .claude/rules/ にルールファイルをシンボリックリンク"
  echo ""
  echo "  team      チームプロジェクト用セットアップ"
  echo "            - CLAUDE.local.md を作成（.gitignore に追記）"
  echo "            - .claude/rules/ にルールファイルをコピー（.gitignore に追記）"
  exit 1
}

setup_rules_dir() {
  mkdir -p "${PROJECT_DIR}/.claude/rules"
}

link_rules() {
  local mode="$1"
  for rule_file in "${SCRIPT_DIR}/rules/"*.md; do
    local basename
    basename="$(basename "$rule_file")"
    local target="${PROJECT_DIR}/.claude/rules/${basename}"

    if [ -e "$target" ]; then
      echo "  skip: .claude/rules/${basename} (already exists)"
      continue
    fi

    if [ "$mode" = "link" ]; then
      ln -s "$rule_file" "$target"
      echo "  link: .claude/rules/${basename}"
    else
      cp "$rule_file" "$target"
      echo "  copy: .claude/rules/${basename}"
    fi
  done
}

add_to_gitignore() {
  local entry="$1"
  if [ -f "${PROJECT_DIR}/.gitignore" ]; then
    if ! grep -qF "$entry" "${PROJECT_DIR}/.gitignore"; then
      echo "$entry" >> "${PROJECT_DIR}/.gitignore"
      echo "  .gitignore: added ${entry}"
    fi
  else
    echo "$entry" > "${PROJECT_DIR}/.gitignore"
    echo "  .gitignore: created with ${entry}"
  fi
}

setup_hooks() {
  local settings_dir="${PROJECT_DIR}/.claude"
  local settings_file="${settings_dir}/settings.json"
  mkdir -p "$settings_dir"

  # .env.issue-index があればhookを設定
  if [ -f "${PROJECT_DIR}/.env.issue-index" ]; then
    local sync_script="${SCRIPT_DIR}/skills/issue-index/sync.sh"
    if [ -f "$settings_file" ]; then
      # 既にhooksがあればスキップ
      if jq -e '.hooks' "$settings_file" > /dev/null 2>&1; then
        echo "  skip: hooks (already configured in .claude/settings.json)"
      else
        # 既存のsettings.jsonにhooksを追加
        local tmp
        tmp=$(mktemp)
        jq --arg cmd "bash ${sync_script} ." \
          '. + {hooks: {SessionStart: [{hooks: [{type: "command", command: $cmd}]}]}}' \
          "$settings_file" > "$tmp" && mv "$tmp" "$settings_file"
        echo "  update: .claude/settings.json (hooks added)"
      fi
    else
      # settings.jsonを新規作成
      jq -n --arg cmd "bash ${sync_script} ." \
        '{hooks: {SessionStart: [{hooks: [{type: "command", command: $cmd}]}]}}' \
        > "$settings_file"
      echo "  create: .claude/settings.json (with hooks)"
    fi
  fi
}

setup_personal() {
  echo "=== Personal project setup ==="
  echo "Project: ${PROJECT_DIR}"
  echo ""

  setup_rules_dir
  link_rules "link"
  setup_hooks

  echo ""
  echo "Done. rules/ はシンボリックリンク。プロジェクト固有ルールは .claude/rules/ に直接追加可能。"
}

setup_team() {
  echo "=== Team project setup ==="
  echo "Project: ${PROJECT_DIR}"
  echo ""

  # CLAUDE.local.md
  local local_md="${PROJECT_DIR}/CLAUDE.local.md"
  if [ -e "$local_md" ]; then
    echo "  skip: CLAUDE.local.md (already exists)"
  else
    cat > "$local_md" <<'LOCALMD'
# ローカル設定（個人用・gitignore対象）

# プロジェクト固有の個人設定をここに書く
LOCALMD
    echo "  create: CLAUDE.local.md"
  fi
  add_to_gitignore "CLAUDE.local.md"

  # rules/
  setup_rules_dir
  link_rules "copy"
  add_to_gitignore ".claude/rules/"

  echo ""
  echo "Done. CLAUDE.local.md と .claude/rules/ は .gitignore 済み。"
}

# main
if [ $# -ne 1 ]; then
  usage
fi

case "$1" in
  personal) setup_personal ;;
  team)     setup_team ;;
  *)        usage ;;
esac
