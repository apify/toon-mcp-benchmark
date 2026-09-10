#!/usr/bin/env bash
# Render charts/fig*.svg to PNG with agent-browser (headless Chromium).
# Each SVG is wrapped in a minimal HTML page and the <img> element is screenshotted, so the PNG box equals the SVG box
# (device scale factor is the browser default). Usage: bash charts/render_png.sh   Requires: agent-browser, python3.
set -euo pipefail
cd "$(dirname "$0")"
for svg in fig*.svg; do
  read -r w h < <(python3 -c "import re;s=open('$svg').read();print(re.search(r'width=\"(\d+)\"',s).group(1),re.search(r'height=\"(\d+)\"',s).group(1))")
  printf '<!doctype html><html><body style="margin:0;background:#fff"><img id="fig" src="%s" width="%s" height="%s"></body></html>' "$svg" "$w" "$h" > "_render_${svg%.svg}.html"
  agent-browser open "file://$PWD/_render_${svg%.svg}.html" >/dev/null
  agent-browser wait 500 >/dev/null 2>&1 || true
  agent-browser screenshot "#fig" "$PWD/${svg%.svg}.png" >/dev/null
  rm -f "_render_${svg%.svg}.html"
  echo "${svg%.svg}.png <- $svg (${w}x${h} CSS px)"
done
agent-browser close >/dev/null 2>&1 || true
file fig*.png | sed 's/, 8-bit.*//'
