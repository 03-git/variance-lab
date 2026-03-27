#!/bin/bash
# Local Variance Lab — Batch Runner
# Runs all prompts against all specified models via Ollama and/or LM Studio.
# Models are configured in models.conf (endpoint:model_name:tier)
#
# Usage: ./run-local-batch.sh [--dry-run] [--endpoint ollama|lmstudio] [--tier execution|reasoning|research] [--passes N]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODELS_CONF="${SCRIPT_DIR}/models.conf"
PROMPTS_DIR="${SCRIPT_DIR}/prompts"

DRY_RUN=""
PASSES=1
ENDPOINT_FILTER=""
TIER_FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)    DRY_RUN="--dry-run"; shift ;;
    --passes)     PASSES="$2"; shift 2 ;;
    --endpoint)   ENDPOINT_FILTER="$2"; shift 2 ;;
    --tier)       TIER_FILTER="$2"; shift 2 ;;
    *)            echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ ! -f "${MODELS_CONF}" ]]; then
  echo "ERROR: ${MODELS_CONF} not found." >&2
  exit 1
fi

# Read models (format: endpoint:model_name:tier)
ENTRIES=()
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  ENDPOINT="${line%%:*}"
  REST="${line#*:}"
  MODEL="${REST%:*}"
  TIER="${REST##*:}"

  if [[ -n "${ENDPOINT_FILTER}" && "${ENDPOINT}" != "${ENDPOINT_FILTER}" ]]; then continue; fi
  if [[ -n "${TIER_FILTER}" && "${TIER}" != "${TIER_FILTER}" ]]; then continue; fi

  ENTRIES+=("${ENDPOINT}:${MODEL}:${TIER}")
done < "${MODELS_CONF}"

# Read prompts
PROMPT_FILES=()
for f in "${PROMPTS_DIR}"/*.md; do
  [[ -f "$f" ]] && PROMPT_FILES+=("$f")
done

TOTAL_SIMS=$((${#ENTRIES[@]} * ${#PROMPT_FILES[@]} * PASSES))

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
RUN_DIR="${SCRIPT_DIR}/output/run-${TIMESTAMP}"
mkdir -p "${RUN_DIR}"

# Write run manifest
cat > "${RUN_DIR}/manifest.json" << MANIFEST
{
  "timestamp": "${TIMESTAMP}",
  "passes": ${PASSES},
  "models": ${#ENTRIES[@]},
  "prompts": ${#PROMPT_FILES[@]},
  "total_sims": ${TOTAL_SIMS},
  "endpoint_filter": "${ENDPOINT_FILTER}",
  "tier_filter": "${TIER_FILTER}",
  "dry_run": $([ -n "${DRY_RUN}" ] && echo "true" || echo "false")
}
MANIFEST

echo "╔══════════════════════════════════════════════════╗"
echo "║       Local Variance Lab — Batch Run             ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║ Models:    ${#ENTRIES[@]}"
echo "║ Prompts:   ${#PROMPT_FILES[@]}"
echo "║ Passes:    ${PASSES}"
echo "║ Total:     ${TOTAL_SIMS} simulations"
echo "║ Output:    ${RUN_DIR}"
if [[ -n "${TIER_FILTER}" ]]; then
echo "║ Tier:      ${TIER_FILTER}"
fi
if [[ -n "${DRY_RUN}" ]]; then
echo "║ MODE:      DRY RUN"
fi
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Print model list with tiers
echo "Models:"
for ENTRY in "${ENTRIES[@]}"; do
  ENDPOINT="${ENTRY%%:*}"
  REST="${ENTRY#*:}"
  MODEL="${REST%:*}"
  TIER="${REST##*:}"
  echo "  [${TIER}] ${MODEL} (${ENDPOINT})"
done
echo ""

TOTAL_START=$SECONDS

for PASS in $(seq 1 "${PASSES}"); do
  echo "━━━ Pass ${PASS}/${PASSES} ━━━"

  for ENTRY in "${ENTRIES[@]}"; do
    ENDPOINT="${ENTRY%%:*}"
    REST="${ENTRY#*:}"
    MODEL="${REST%:*}"
    TIER="${REST##*:}"

    for PROMPT_FILE in "${PROMPT_FILES[@]}"; do
      PROMPT_NAME=$(basename "${PROMPT_FILE}" .md)
      PASS_DIR="${RUN_DIR}/pass-${PASS}/${PROMPT_NAME}"
      mkdir -p "${PASS_DIR}"

      echo "  [${TIER}] ${MODEL} | ${PROMPT_NAME}"

      python3 "${SCRIPT_DIR}/run-local-single.py" \
        --model "${MODEL}" \
        --prompt-file "${PROMPT_FILE}" \
        --output-dir "${PASS_DIR}" \
        --endpoint "${ENDPOINT}" \
        --tier "${TIER}" \
        ${DRY_RUN}
    done
  done
done

ELAPSED=$((SECONDS - TOTAL_START))

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  Complete: ${ELAPSED}s"
echo "╚══════════════════════════════════════════════════╝"

# Generate summary if not dry run
if [[ -z "${DRY_RUN}" ]]; then
  python3 "${SCRIPT_DIR}/aggregate-local.py" "${RUN_DIR}" "${PASSES}"
fi
