#!/usr/bin/env bash
# Re-create focus-math/repos from the pinned commits in LOCK.tsv.
#
#   bash focus-math/fetch.sh          # checkout the locked commits
#   bash focus-math/fetch.sh --init   # clone default branches, write LOCK.tsv
#
# Clones are shallow (depth 1) and stay out of git. Nothing here is built or
# imported by clothoid_lab; it is reading material.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
REPOS="$ROOT/repos"
LOCK="$ROOT/LOCK.tsv"

REPOS_LIST=$(cat <<'LIST'
G1fitting	https://github.com/ebertolazzi/G1fitting
pyclothoids	https://github.com/phillipd94/pyclothoids
euler_spiral	https://github.com/CoffeeKumazaki/euler_spiral
qaws	https://github.com/soufianekhiat/qaws
spiro	https://github.com/raphlinus/spiro
kurbo	https://github.com/linebender/kurbo
paperjs-offset	https://github.com/glenzli/paperjs-offset
cubic-bezier-offsetter	https://github.com/aurimasg/cubic-bezier-offsetter
Clipper2	https://github.com/AngusJohnson/Clipper2
Violin_Boundary	https://github.com/Mathias1211/Violin_Boundary
LIST
)

mkdir -p "$REPOS"

clone_default() {
  local name=$1 url=$2 dir="$REPOS/$1"
  [ -d "$dir" ] && return
  echo "clone  $name"
  git clone --depth 1 --quiet "$url" "$dir"
}

if [ "${1:-}" = "--init" ]; then
  : > "$LOCK"
  while IFS=$'\t' read -r name url; do
    clone_default "$name" "$url"
    printf '%s\t%s\t%s\n' "$name" "$url" \
      "$(git -C "$REPOS/$name" rev-parse HEAD)" >> "$LOCK"
  done <<< "$REPOS_LIST"
  echo "wrote $LOCK"
  exit 0
fi

[ -f "$LOCK" ] || { echo "no LOCK.tsv; run: bash focus-math/fetch.sh --init" >&2; exit 1; }

while IFS=$'\t' read -r name url commit; do
  dir="$REPOS/$name"
  if [ ! -d "$dir" ]; then
    echo "clone  $name"
    git clone --quiet --filter=blob:none --no-checkout "$url" "$dir"
  fi
  git -C "$dir" fetch --quiet --depth 1 origin "$commit"
  git -C "$dir" checkout --quiet "$commit"
  echo "ok     $name @ ${commit:0:9}"
done < "$LOCK"
