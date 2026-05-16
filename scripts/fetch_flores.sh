#!/usr/bin/env bash
# Download FLORES-200 dev + devtest files we need (yue_Hant + zho_Hans).
# Source: https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz (25MB)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/data/flores"
TARBALL=/tmp/flores200.tar.gz

mkdir -p "$DEST"

if [[ ! -f "$TARBALL" ]]; then
    echo "Downloading FLORES-200 dataset (25 MB)…"
    curl -L "https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz" \
         -o "$TARBALL"
fi

echo "Extracting yue_Hant + zho_Hans files…"
tar -xzf "$TARBALL" -C /tmp/ \
    ./flores200_dataset/dev/yue_Hant.dev \
    ./flores200_dataset/dev/zho_Hans.dev \
    ./flores200_dataset/devtest/yue_Hant.devtest \
    ./flores200_dataset/devtest/zho_Hans.devtest

cp /tmp/flores200_dataset/dev/yue_Hant.dev \
   /tmp/flores200_dataset/dev/zho_Hans.dev \
   /tmp/flores200_dataset/devtest/yue_Hant.devtest \
   /tmp/flores200_dataset/devtest/zho_Hans.devtest \
   "$DEST/"

echo "✓ FLORES files in $DEST:"
ls -la "$DEST"
echo
echo "Note: FLORES-200 does NOT include Hokkien (nan_*). We use yue_Hant"
echo "(Cantonese) as a Chinese-language-family proxy. See HONESTY.md."
