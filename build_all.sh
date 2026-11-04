#!/bin/bash
# Build the msys_viparr conda package for every python version in
# recipe/variants.yaml and write a local conda channel to ./output/channel.
#
#   ./build_all.sh                # all variants
#   ./build_all.sh 3.12           # one variant
#
# Needs rattler-build on PATH (conda install -c conda-forge rattler-build).
# Set CHANNEL to use a conda-forge mirror, e.g.
#   CHANNEL=https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge ./build_all.sh 3.12
set -euo pipefail
cd "$(dirname "$0")"

OUT=output/channel
mkdir -p "$OUT"
CHANNEL=${CHANNEL:-conda-forge}

args=(build --recipe recipe --output-dir "$OUT" -c "$CHANNEL" --channel-priority strict)
if [ $# -gt 0 ]; then
    # restrict the python variant
    printf 'python:\n  - "%s"\n' "$1" > output/variants-one.yaml
    args+=(--variant-config output/variants-one.yaml)
else
    args+=(--variant-config recipe/variants.yaml)
fi

rattler-build "${args[@]}"

echo
echo "Packages:"
ls -1 "$OUT"/*/msys_viparr-*.conda
echo
echo "Install with:"
echo "  conda create -n msys -c $(pwd)/$OUT -c $CHANNEL msys_viparr python=3.12"
