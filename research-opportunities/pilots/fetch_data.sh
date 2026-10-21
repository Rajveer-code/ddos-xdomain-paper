#!/usr/bin/env bash
# Clone the two public datasets the pilots read, at the commits the results were produced from.
set -euo pipefail
DEST="${1:-./data}"
mkdir -p "$DEST"

fetch() {  # url dir commit
  if [ ! -d "$DEST/$2/.git" ]; then
    git clone --filter=blob:none "$1" "$DEST/$2"
  fi
  git -C "$DEST/$2" checkout -q "$3"
}

fetch https://github.com/ethz-spylab/agentdojo agentdojo 089ed468cf3ed0322acc66b0211f26d9d90dbf60
fetch https://github.com/JailbreakBench/artifacts jbb_artifacts 909e68c01d94222b8ad2e397a017e2e12e2adb73
echo "data in $DEST"
