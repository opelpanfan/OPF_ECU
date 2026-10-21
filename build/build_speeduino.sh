#!/usr/bin/env bash
# Moved to scripts/speeduino/build_speeduino.sh (same layout as scripts/rusefi, scripts/fome).
# Compatibility shim for existing local invocations; all arguments are passed through.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/scripts/speeduino/build_speeduino.sh" "$@"
