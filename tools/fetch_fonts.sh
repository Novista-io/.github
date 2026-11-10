#!/bin/sh
# Downloads the three website fonts (SIL Open Font License) that tools/build.py
# turns into outlines. They are not committed; only the generated SVGs are.
set -e
cd "$(dirname "$0")"
mkdir -p fonts
base=https://raw.githubusercontent.com/google/fonts/main/ofl
curl -sfL "$base/bricolagegrotesque/BricolageGrotesque%5Bopsz,wdth,wght%5D.ttf" -o fonts/BricolageGrotesque.ttf
curl -sfL "$base/geist/Geist%5Bwght%5D.ttf" -o fonts/Geist.ttf
curl -sfL "$base/archivo/Archivo%5Bwdth,wght%5D.ttf" -o fonts/Archivo.ttf
echo "fonts ready in tools/fonts"
