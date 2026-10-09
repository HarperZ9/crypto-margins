#!/usr/bin/env bash
# Build g6k from github.com/fplll/g6k into ~/cm/g6kenv. The PyPI sdist fails
# under Cython 3 (LambdaNode serializer error in siever.pyx, 2026-10-08).
set -eu
ENV="$HOME/cm/g6kenv"
"$ENV/bin/python" -c "import fpylll; print('fpylll', fpylll.__version__)"
SRC="$HOME/cm/g6k-src"
rm -rf "$SRC"
git clone -q --depth 1 https://github.com/fplll/g6k.git "$SRC"
git -C "$SRC" log -1 --format='g6k commit %H %cd'
cd "$SRC"
"$ENV/bin/pip" install -q -r requirements.txt || true
"$ENV/bin/pip" install -q --no-build-isolation .
cd /
"$ENV/bin/python" - <<'EOF'
import g6k
from g6k import Siever
print("g6k ok", g6k.__file__)
EOF
