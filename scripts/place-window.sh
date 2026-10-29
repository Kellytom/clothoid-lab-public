#!/bin/bash
# scripts/place-window.sh — put the Inkscape window on one half of the screen.
#
# Window position is application state, not document state, so it cannot be
# written into the SVG the way the zoom can. This drives System Events instead.
#
# The first run needs permission: System Settings > Privacy & Security >
# Accessibility, and allow whichever app launches this (Terminal, or the editor
# that runs it). Without that, osascript returns an error about assistive
# access rather than moving anything.
#
#   scripts/place-window.sh right    the default
#   scripts/place-window.sh left
#   scripts/place-window.sh top
#   scripts/place-window.sh bottom

set -euo pipefail

SIDE="${1:-right}"

osascript - "$SIDE" <<'EOS'
on run argv
  set side to item 1 of argv

  tell application "System Events"
    if not (exists process "Inkscape") then
      error "Inkscape is not running"
    end if
    tell process "Inkscape" to set frontmost to true
  end tell

  tell application "Finder"
    set {dx, dy, dw, dh} to bounds of window of desktop
  end tell

  set halfW to (dw / 2) as integer
  set halfH to (dh / 2) as integer
  set topGap to 25

  if side is "left" then
    set {px, py, pw, ph} to {0, topGap, halfW, dh - topGap}
  else if side is "top" then
    set {px, py, pw, ph} to {0, topGap, dw, halfH - topGap}
  else if side is "bottom" then
    set {px, py, pw, ph} to {0, halfH, dw, dh - halfH}
  else
    set {px, py, pw, ph} to {halfW, topGap, halfW, dh - topGap}
  end if

  tell application "System Events"
    tell process "Inkscape"
      set position of window 1 to {px, py}
      set size of window 1 to {pw, ph}
    end tell
  end tell
end run
EOS
