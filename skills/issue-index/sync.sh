#!/bin/bash
# Issue Index Sync Script
# gh issue list + GraphQL(Projects status) → .issue-index.json
#
# Usage: sync.sh [project-dir]
#   project-dir: .env.issue-index があるディレクトリ（デフォルト: カレントディレクトリ）

set -euo pipefail

PROJECT_DIR="${1:-.}"
ENV_FILE="$PROJECT_DIR/.env.issue-index"

if [ ! -f "$ENV_FILE" ]; then
  echo "Error: $ENV_FILE not found" >&2
  exit 1
fi

# shellcheck source=/dev/null
source "$ENV_FILE"

: "${REPO:?REPO is required in .env.issue-index}"
: "${PROJECT_NUMBER:?PROJECT_NUMBER is required in .env.issue-index}"
: "${OWNER:?OWNER is required in .env.issue-index}"

OUTPUT_FILE="$PROJECT_DIR/.issue-index.json"

# GraphQLで全Issueをステータス付きで取得（100件まで）
QUERY='
{
  user(login: "'"$OWNER"'") {
    projectV2(number: '"$PROJECT_NUMBER"') {
      items(first: 100) {
        nodes {
          fieldValueByName(name: "Status") {
            ... on ProjectV2ItemFieldSingleSelectValue { name }
          }
          content {
            ... on Issue {
              number
              title
              state
              labels(first: 10) { nodes { name } }
            }
          }
        }
      }
    }
  }
}'

RAW=$(gh api graphql -f query="$QUERY" --jq '
  .data.user.projectV2.items.nodes
  | map(select(.content.number != null))
  | map({
      number: .content.number,
      title: .content.title,
      state: .content.state,
      labels: [.content.labels.nodes[].name],
      status: (.fieldValueByName.name // "Unknown")
    })
  | sort_by(.number)
')

# JSON生成
jq -n \
  --arg updated_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg repo "$REPO" \
  --argjson issues "$RAW" \
  '{updated_at: $updated_at, repo: $repo, issues: $issues}' \
  > "$OUTPUT_FILE"

COUNT=$(echo "$RAW" | jq 'length')
echo "Synced $COUNT issues to $OUTPUT_FILE"
