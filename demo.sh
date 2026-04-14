#!/usr/bin/env bash
# Quick smoke test — verifies all 3 scripts work.
# Usage: bash demo.sh
set -e

echo "==> Installing deps..."
pip install -q Pillow scipy requests numpy 2>/dev/null

echo "==> Photo conversion (pixelart.py)..."
python scripts/pixelart.py -h > /dev/null 2>&1 && echo "    pixelart.py OK" || { echo "    pixelart.py FAIL"; exit 1; }

echo "==> Image generation (pixelart_image.py)..."
python scripts/pixelart_image.py "a pixel art cat sleeping" --tech nes -o ./pixelart_output/demo_image.png && echo "    pixelart_image.py OK → ./pixelart_output/demo_image.png" || { echo "    pixelart_image.py FAIL"; exit 1; }

echo "==> Video generation (pixelart_video.py)..."
python scripts/pixelart_video.py "stars over a lake" --scene night --duration 3 --gif -o ./pixelart_output/demo_video.mp4 && echo "    pixelart_video.py OK → ./pixelart_output/demo_video.mp4 + .gif" || { echo "    pixelart_video.py FAIL"; exit 1; }

echo ""
echo "✅ All scripts working. Outputs in ./pixelart_output/"
