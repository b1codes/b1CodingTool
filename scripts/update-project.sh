#!/bin/bash
set -uo pipefail

# Keeps coding-agent tooling current for the project this script is run in.
#
#   - Claude Code:   refreshes plugin marketplaces, then updates every
#                     installed plugin.
#   - Antigravity:   updates plugins via the community agy-plugins-cli
#                     wrapper if present, otherwise lists installed plugins
#                     (native agy has no bulk plugin-update command yet).
#   - Codex CLI:     refreshes plugin marketplaces (`codex plugin marketplace
#                     upgrade`), then re-adds every installed plugin (`codex
#                     plugin add <id> --marketplace <name>`) to pull the
#                     refreshed snapshot — codex has no separate
#                     `plugin update` verb; re-adding is the update mechanism.
#   - Common step:   runs `npx skills update` in the current directory.
#
# Usage: update-project.sh [--claude] [--agy] [--codex] [--all] [--skip-skills]

SCRIPT_NAME="$(basename "$0")"
RUN_CLAUDE=""
RUN_AGY=""
RUN_CODEX=""
SKIP_SKILLS=0
EXPLICIT=0

usage() {
  cat <<EOF
Usage: $SCRIPT_NAME [--claude] [--agy] [--codex] [--all] [--skip-skills]

  (no flags)     Auto-detect: update whichever of 'claude' / 'agy' / 'codex' are on PATH.
  --claude       Only run the Claude Code plugin/marketplace update.
  --agy          Only run the Antigravity CLI plugin update.
  --codex        Only run the Codex CLI plugin/marketplace update.
  --all          Run Claude Code, Antigravity, and Codex CLI updates explicitly.
  --skip-skills  Skip the 'npx skills update' step.
  -h, --help     Show this help.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --claude) RUN_CLAUDE=1; EXPLICIT=1 ;;
    --agy) RUN_AGY=1; EXPLICIT=1 ;;
    --codex) RUN_CODEX=1; EXPLICIT=1 ;;
    --all) RUN_CLAUDE=1; RUN_AGY=1; RUN_CODEX=1; EXPLICIT=1 ;;
    --skip-skills) SKIP_SKILLS=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; usage >&2; exit 1 ;;
  esac
done

if [ "$EXPLICIT" -eq 0 ]; then
  command -v claude >/dev/null 2>&1 && RUN_CLAUDE=1
  command -v agy >/dev/null 2>&1 && RUN_AGY=1
  command -v codex >/dev/null 2>&1 && RUN_CODEX=1
fi

update_claude() {
  if ! command -v claude >/dev/null 2>&1; then
    echo "==> claude CLI not found on PATH, skipping Claude Code update." >&2
    return 0
  fi

  echo "==> Refreshing Claude Code plugin marketplaces..."
  claude plugin marketplace update || echo "    Warning: marketplace update failed." >&2

  echo "==> Updating installed Claude Code plugins..."
  local plugin_json
  plugin_json="$(claude plugin list --json 2>/dev/null)" || plugin_json="[]"

  local ids=""
  if command -v jq >/dev/null 2>&1; then
    ids="$(printf '%s' "$plugin_json" | jq -r '.[].id' 2>/dev/null)"
  elif command -v node >/dev/null 2>&1; then
    ids="$(printf '%s' "$plugin_json" | node -e '
      let data = "";
      process.stdin.on("data", c => data += c);
      process.stdin.on("end", () => {
        try {
          JSON.parse(data).forEach(p => { if (p && p.id) console.log(p.id); });
        } catch (e) {}
      });
    ')"
  else
    echo "    Warning: neither jq nor node is available to parse plugin list; skipping plugin updates." >&2
    return 0
  fi

  if [ -z "$ids" ]; then
    echo "    No installed plugins found."
    return 0
  fi

  while IFS= read -r id; do
    [ -z "$id" ] && continue
    echo "    Updating $id..."
    claude plugin update "$id" -y || echo "    Warning: failed to update $id" >&2
  done <<< "$ids"
}

update_agy() {
  if ! command -v agy >/dev/null 2>&1; then
    echo "==> agy CLI not found on PATH, skipping Antigravity update." >&2
    return 0
  fi

  if command -v agy-plugin >/dev/null 2>&1; then
    echo "==> Updating Antigravity plugins via agy-plugins-cli wrapper..."
    agy-plugin update || echo "    Warning: agy-plugin update failed." >&2
  else
    echo "==> agy-plugins-cli (agy-plugin) not found on PATH."
    echo "    Native agy has no bulk plugin-update command yet; listing installed plugins instead:"
    agy plugin list || echo "    Warning: failed to list agy plugins." >&2
    echo "    Install the community wrapper for bulk updates: npm install -g agy-plugins-cli"
  fi
}

update_codex() {
  if ! command -v codex >/dev/null 2>&1; then
    echo "==> codex CLI not found on PATH, skipping Codex CLI update." >&2
    return 0
  fi

  echo "==> Refreshing Codex plugin marketplaces..."
  codex plugin marketplace upgrade || echo "    Warning: marketplace upgrade failed." >&2

  echo "==> Updating installed Codex plugins..."
  local plugin_json
  plugin_json="$(codex plugin list --json 2>/dev/null)" || plugin_json="{}"

  local pairs=""
  if command -v jq >/dev/null 2>&1; then
    pairs="$(printf '%s' "$plugin_json" | jq -r '.installed[]? | "\(.pluginId)\t\(.marketplaceName)"' 2>/dev/null)"
  elif command -v node >/dev/null 2>&1; then
    pairs="$(printf '%s' "$plugin_json" | node -e '
      let data = "";
      process.stdin.on("data", c => data += c);
      process.stdin.on("end", () => {
        try {
          (JSON.parse(data).installed || []).forEach(p => {
            if (p && p.pluginId) console.log(`${p.pluginId}\t${p.marketplaceName}`);
          });
        } catch (e) {}
      });
    ')"
  else
    echo "    Warning: neither jq nor node is available to parse plugin list; skipping plugin updates." >&2
    return 0
  fi

  if [ -z "$pairs" ]; then
    echo "    No installed plugins found."
    return 0
  fi

  while IFS=$'\t' read -r id marketplace; do
    [ -z "$id" ] && continue
    echo "    Updating $id@$marketplace..."
    codex plugin add "$id" --marketplace "$marketplace" >/dev/null || echo "    Warning: failed to update $id@$marketplace" >&2
  done <<< "$pairs"
}

update_skills() {
  echo "==> Running 'npx skills update' in $(pwd)..."
  npx skills update || echo "    Warning: 'npx skills update' failed." >&2
}

main() {
  if [ -z "$RUN_CLAUDE" ] && [ -z "$RUN_AGY" ] && [ -z "$RUN_CODEX" ]; then
    echo "No coding-agent CLI detected on PATH (claude/agy/codex) and no override flag given." >&2
    echo "Pass --claude, --agy, or --codex to force a specific tool." >&2
  fi

  [ -n "$RUN_CLAUDE" ] && update_claude
  [ -n "$RUN_AGY" ] && update_agy
  [ -n "$RUN_CODEX" ] && update_codex

  if [ "$SKIP_SKILLS" -eq 0 ]; then
    update_skills
  fi

  echo "==> Done."
}

main
