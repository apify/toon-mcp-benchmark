#!/usr/bin/env bash
# Render charts/fig*.svg to PNG with agent-browser (headless Chromium).
# Each SVG is wrapped in a minimal HTML page at 2x its size and the <img> element is screenshotted, so the PNG is exactly
# twice the SVG box (1920px wide) for crisp blog embedding. Usage: bash charts/render_png.sh   Requires: agent-browser, python3.
set -euo pipefail
cd "$(dirname "$0")"
agent-browser close >/dev/null 2>&1 || true
for svg in fig*.svg; do
  read -r w h < <(python3 -c "import re;s=open('$svg').read();print(re.search(r'width=\"(\d+)\"',s).group(1),re.search(r'height=\"(\d+)\"',s).group(1))")
  html="_render_${svg%.svg}.html"
  printf '<!doctype html><html><body style="margin:0;background:#fff"><img id="fig" src="%s" style="display:block;width:%spx;height:%spx"></body></html>' "$svg" $((w * 2)) $((h * 2)) > "$html"
  agent-browser open "file://$PWD/$html" >/dev/null
  agent-browser wait "#fig" >/dev/null 2>&1 || agent-browser wait 1500 >/dev/null 2>&1 || true
  agent-browser screenshot "#fig" "$PWD/${svg%.svg}.png" >/dev/null
  rm -f "$html"
  echo "${svg%.svg}.png <- $svg (${w}x${h} CSS px, rendered at 2x)"
done
agent-browser close >/dev/null 2>&1 || true
file fig*.png | sed 's/, 8-bit.*//'
