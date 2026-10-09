#!/usr/bin/env bash
# Separate venv for g6k, built with Ubuntu's toolchain. The conda-forge
# toolchain fails to link libg6k (undefined __TMC_END__ from crtbeginS.o), and
# PyPI has no g6k wheels (both observed 2026-10-08).
set -eu
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq build-essential python3-dev python3-venv \
  libgmp-dev libmpfr-dev libqd-dev libfplll-dev pkg-config autoconf automake libtool >/dev/null
ENV="$HOME/cm/g6kenv"
python3 -m venv "$ENV"
"$ENV/bin/pip" install -q --upgrade pip setuptools wheel
"$ENV/bin/pip" install -q "cython<3.1" cysignals numpy
"$ENV/bin/pip" install -q --no-build-isolation fpylll
"$ENV/bin/pip" install -q --no-build-isolation g6k
"$ENV/bin/python" - <<'EOF'
import fpylll, g6k
print("g6k ok", g6k.__file__, "fpylll", fpylll.__version__)
EOF
