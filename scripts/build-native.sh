#!/bin/bash
# scripts/build-native.sh — build the native Clothoids library.
#
# macOS: build/libclothoidlab.dylib (Mach-O)
# Linux: build/libclothoidlab.so   (ELF, for servers and CI)
#
# No CMake. The vendored tree is CMake 3.x era and modern CMake rejects its old
# minimum versions; the sources compile cleanly with the system compiler, so the
# build is one compile per file and one link. Objects are kept per platform, so a
# macOS and a Linux build can share the tree without mixing object formats.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CL="$ROOT/vendor/Clothoids"
BUILD="$ROOT/build"

OS="$(uname -s)"
case "$OS" in
  Darwin)
    EXT="dylib"
    LINK_FLAGS=(-dynamiclib -install_name @rpath/libclothoidlab.dylib)
    ;;
  Linux)
    EXT="so"
    LINK_FLAGS=(-shared -pthread)
    ;;
  *)
    echo "unsupported platform: $OS (macOS and Linux are built here)" >&2
    exit 1
    ;;
esac

OUT="$BUILD/libclothoidlab.$EXT"
OBJ="$BUILD/obj-$OS"
CXX="${CXX:-c++}"

# Xcode is needed for clang on macOS; on Linux the system compiler is enough.
if [ "$OS" = "Darwin" ] && [ -z "${DEVELOPER_DIR:-}" ]; then
  if command -v xcode-select >/dev/null 2>&1; then
    DEVELOPER_DIR="$(xcode-select -p 2>/dev/null || true)"
  fi
fi
if [ -n "${DEVELOPER_DIR:-}" ]; then
  export DEVELOPER_DIR
fi

if [ ! -d "$CL/src/Clothoids" ]; then
  echo "vendor/Clothoids is missing. Run: git submodule update --init --recursive" >&2
  exit 1
fi

INCLUDES=(
  "-I$CL/src"
  "-I$CL/submodules/UtilsLite/src"
  "-I$CL/submodules/UtilsLite/ThirdParties/Eigen"
  "-I$CL/submodules/GenericContainer/include"
  "-I$CL/submodules/quarticRootsFlocke/src"
)

INC="${INCLUDES[*]}"
export INC ROOT

mkdir -p "$OBJ"

SOURCES=()
while IFS= read -r f; do SOURCES+=("$f"); done < <(
  ls "$CL"/src/*.cc
  ls "$CL"/submodules/UtilsLite/src/*.cc
  # Support.cc pulls the JSON, TOML and YAML readers, which this build does not
  # need and does not carry. Nothing in the geometry path calls into it.
  ls "$CL"/submodules/GenericContainer/src/*.cc | grep -v GenericContainerSupport
  ls "$CL"/submodules/quarticRootsFlocke/src/*.cc
  ls "$ROOT"/csrc/*.cpp
)

echo "compiling ${#SOURCES[@]} sources with $($CXX --version | head -1)"

compile_one() {
  local f="$1"
  local name
  name="$(echo "${f#"$ROOT"/}" | tr '/' '_' | sed 's/\.cc$/.o/; s/\.cpp$/.o/')"
  # Resumable: an object that is already there is not rebuilt, so a fix to one
  # file does not cost the whole tree. Delete the object directory to force a
  # full build.
  [ -f "$OBJ/$name" ] && return 0
  # shellcheck disable=SC2086
  "$CXX" -std=c++17 -O3 -fPIC -w -include utility $INC -c "$f" -o "$OBJ/$name"
}
export -f compile_one
export CXX OBJ

printf '%s\n' "${SOURCES[@]}" | xargs -P 4 -I{} bash -c 'compile_one "$@"' _ {}

echo "linking $OUT"
"$CXX" -std=c++17 -O3 "${LINK_FLAGS[@]}" -o "$OUT" "$OBJ"/*.o

echo "built $OUT"
