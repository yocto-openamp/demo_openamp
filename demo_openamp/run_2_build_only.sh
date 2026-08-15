#!/usr/bin/env bash
set -euo pipefail

# ninja -C build -t clean CMakeFiles/app.dir/src/main.c.obj

cmake --build build
