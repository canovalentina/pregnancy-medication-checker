#!/usr/bin/env bash
# Run with source .env && ./run_synthea.sh
set -euo pipefail

# Load .env file if it exists
if [[ -f .env ]]; then
  set -a  # automatically export all variables
  source .env
  set +a  # stop automatically exporting
fi

# Defaults (override via environment variables)
JAR_PATH="${JAR_PATH:-./synthea-with-dependencies-custom.jar}"
SEED="${SEED:-12345}"               # seed for random number generator
REFDATE="${REFDATE:-}"              # YYYYMMDD, leave empty to omit -r
GENDER="${GENDER:-}"                # M/F, leave empty to omit -g
AGE_RANGE="${AGE_RANGE:-}"          # min_age-max_age,leave empty to omit -a
MODULES_DIR="${MODULES_DIR:-}"      # modules directory, leave empty to omit -d
STATE="${STATE:-}"                  # state name, leave empty to omit location entirely
POP="${POP:-10}"                 # population size
PROPS_FILE="${PROPS_FILE:-./my.properties}" # properties file
JAVA_OPTS="${JAVA_OPTS:-"-Xms2g -Xmx6g"}"  # Java options

# Optional: create properties if it doesn’t exist
if [[ ! -f "$PROPS_FILE" ]]; then
  cat > "$PROPS_FILE" <<EOF
exporter.fhir.export = true
exporter.fhir.use_stu3 = false
exporter.csv.export = true
random.seed = ${SEED}
EOF
fi

# Base command (no optional flags yet)
CMD=(java $JAVA_OPTS -jar "$JAR_PATH" -s "$SEED" -p "$POP" -c "$PROPS_FILE")

# Append optional flags only if set
if [[ -n "${REFDATE:-}" ]]; then
  CMD+=(-r "$REFDATE")
fi
if [[ -n "${GENDER:-}" ]]; then
  CMD+=(-g "$GENDER")
fi
if [[ -n "${AGE_RANGE:-}" ]]; then
  CMD+=(-a "$AGE_RANGE")
fi
if [[ -n "${MODULES_DIR:-}" ]]; then
  CMD+=(-d "$MODULES_DIR")
fi
if [[ -n "${STATE:-}" ]]; then
  CMD+=("$STATE")
fi

echo "Configuration:"
echo "  Population: $POP"
echo "  Gender: ${GENDER:-all}"
echo "  Age Range: ${AGE_RANGE:-all}"
echo "  Modules: ${MODULES_DIR:-default}"
echo "  State: ${STATE:-none}"
echo "  Seed: $SEED"
echo ""
echo "Running:"
printf '%q ' "${CMD[@]}"; echo
echo

# Run
"${CMD[@]}"