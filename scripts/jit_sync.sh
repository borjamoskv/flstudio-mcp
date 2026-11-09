#!/usr/bin/env bash
# ==============================================================================
# JIT Sync Guard - flstudio-mcp Sovereign Resilience Pipeline
# Architecture: Cambio 2 / Topological Jump
# ==============================================================================
set -euo pipefail

REPO_OWNER="borjamoskv"
REPO_NAME="flstudio-mcp"
REPO_FULL="${REPO_OWNER}/${REPO_NAME}"
LOCAL_MIRROR_DIR="${HOME}/Music/.git_mirrors"
BUNDLE_PATH="${LOCAL_MIRROR_DIR}/${REPO_NAME}.bundle"

echo "=== [JIT SYNC GUARD] Initiating Sovereign Transport Audit ==="

# 1. Local Sovereign Mirror Backup (Zero-SPOF Invariant)
mkdir -p "${LOCAL_MIRROR_DIR}"
echo "-> Creating/Updating local sovereign bundle in ${BUNDLE_PATH}..."
git bundle create "${BUNDLE_PATH}.tmp" --all >/dev/null 2>&1 || true
if [ -f "${BUNDLE_PATH}.tmp" ]; then
    mv "${BUNDLE_PATH}.tmp" "${BUNDLE_PATH}"
    echo "✓ Sovereign local bundle secured: ${BUNDLE_PATH}"
fi

# 2. Inspect GitHub Remote Archive Status
echo "-> Querying GitHub API for ${REPO_FULL}..."
IS_ARCHIVED=$(gh api "repos/${REPO_FULL}" --jq '.archived' 2>/dev/null || echo "unknown")

WAS_ARCHIVED=false
if [ "${IS_ARCHIVED}" == "true" ]; then
    echo "⚠️ Remote is ARCHIVED (Read-Only). Activating JIT Unarchive Window..."
    gh api -X PATCH "repos/${REPO_FULL}" -F archived=false >/dev/null
    WAS_ARCHIVED=true
    echo "✓ JIT Unarchive Window OPENED."
elif [ "${IS_ARCHIVED}" == "false" ]; then
    echo "✓ Remote is ACTIVE."
else
    echo "⚠️ Unable to query GitHub API. Proceeding with standard push attempt..."
fi

# 3. Execute Git Push
echo "-> Transporting commits to origin main..."
git push origin main

# 4. Post-Push Lock (Immutable-at-Rest Enforcement if required)
if [ "${WAS_ARCHIVED}" == "true" ] && [ "${1:-}" == "--rearchive" ]; then
    echo "-> Re-archiving remote repository (Immutable-at-Rest)..."
    gh api -X PATCH "repos/${REPO_FULL}" -F archived=true >/dev/null
    echo "✓ Remote re-archived."
fi

echo "=== [JIT SYNC GUARD] Synchronized with High Exergy ==="
