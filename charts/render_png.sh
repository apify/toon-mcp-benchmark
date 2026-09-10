#!/usr/bin/env bash
# Render charts/fig*.svg to PNG with agent-browser (headless Chromium).
# Each SVG is wrapped in a minimal HTML page and the <img> element is screenshotted, so the PNG box equals the SVG box
# rendered at 2× the SVG size for crisp blog embedding. Usage: bash charts/render_png.sh   Requires: agent-browser, python3.
set -euo pipefail
cd "$(dirname "$0")"
for svg in fig*.svg; do
  read -r w h < <(python3 -c "import re;s=open('$svg').read();print(re.search(r'width=\"(\d+)\"',s).group(1),re.search(r'height=\"(\d+)\"',s).group(1))")
  printf '<!doctype html><html><body style="margin:0;background:#fff"><img id="fig" src="%s" width="%s" height="%s" style="width:calc(%spx * 2);height:calc(%spx * 2)"></body></html>' "$svg" "$w" "$h" "$w" "$h" > "_render_${svg%.svg}.html"
  agent-browser close >/dev/null 2>&1 || true   # viewport flags apply at launch
  agent-browser open "file://$PWD/_render_${svg%.svg}.html" --viewport-width $((w * 2 + 40)) --viewport-height $((h * 2 + 40)) >/dev/null
  agent-browser wait "#fig" >/dev/null
  agent-browser screenshot "#fig" "$PWD/${svg%.svg}.png" >/dev/null
  rm -f "_render_${svg%.svg}.html"
  echo "${svg%.svg}.png <- $svg (${w}x${h} CSS px)"
done
agent-browser close >/dev/null 2>&1 || true
file fig*.png | sed 's/, 8-bit.*//'
