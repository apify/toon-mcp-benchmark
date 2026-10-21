#!/usr/bin/env bash
# Render charts/fig*.svg to PNG with agent-browser (headless Chromium) at 2x device scale.
# Each SVG is inlined into a minimal HTML page that loads Inter from Google Fonts (an <img>-embedded SVG
# cannot use web fonts), the viewport is set to the SVG size with scale factor 2, and the <svg> element is
# screenshotted: the PNG is exactly twice the SVG box (1920px wide), nothing clipped.
# Usage: bash charts/render_png.sh   Requires: agent-browser (npm i -g agent-browser), python3, network for the font.
set -euo pipefail
cd "$(dirname "$0")"
agent-browser close >/dev/null 2>&1 || true
for svg in fig*.svg; do
  read -r w h < <(python3 -c "import re;s=open('$svg').read();print(re.search(r'width=\"(\d+)\"',s).group(1),re.search(r'height=\"(\d+)\"',s).group(1))")
  html="_render_${svg%.svg}.html"
  python3 - "$svg" "$html" <<'PY'
import sys
svg, html = sys.argv[1], sys.argv[2]
body = open(svg).read().replace("<svg ", '<svg id="fig" style="display:block" ', 1)
open(html, "w").write('<!doctype html><html><head><meta charset="utf-8">'
  '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=block">'
  '</head><body style="margin:0;background:#1F2123">' + body + '</body></html>')
PY
  agent-browser open "file://$PWD/$html" >/dev/null
  agent-browser set viewport "$w" "$h" 2 >/dev/null   # resets the page, so open again
  agent-browser open "file://$PWD/$html" >/dev/null
  agent-browser eval "document.fonts.ready.then(() => document.fonts.check('600 13px Inter'))" >/dev/null 2>&1 || true
  agent-browser wait 800 >/dev/null 2>&1 || true
  agent-browser screenshot "#fig" "$PWD/${svg%.svg}.png" >/dev/null
  rm -f "$html"
  echo "${svg%.svg}.png <- $svg (${w}x${h} CSS px @2x)"
done
agent-browser close >/dev/null 2>&1 || true
file fig*.png | sed 's/, 8-bit.*//'
