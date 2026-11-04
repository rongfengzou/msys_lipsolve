#!/bin/bash
set -ex

# sconsutils.py (DESRES scons extensions) lives in external/
export PYTHONPATH=$SRC_DIR/external:$PYTHONPATH

# scons reads the compiler flags from these DESRES_MODULE_* variables.
# conda-forge lp_solve installs its headers under include/lpsolve; msys falls
# back to <lp_lib.h> when <lp_solve/lp_lib.h> is absent, so just add the dir.
export DESRES_MODULE_CXXFLAGS="$CXXFLAGS -I$PREFIX/include -I$PREFIX/include/lpsolve"
export DESRES_MODULE_CFLAGS="$CFLAGS -I$PREFIX/include -I$PREFIX/include/lpsolve"
export DESRES_MODULE_LDFLAGS="$LDFLAGS -L$PREFIX/lib"

# bliss-0.73.zip has a single top-level dir; cope with either extraction layout
if [ -d external/bliss/bliss-0.73/bliss-0.73 ]; then
    mv external/bliss/bliss-0.73/bliss-0.73/* external/bliss/bliss-0.73/
    rmdir external/bliss/bliss-0.73/bliss-0.73
fi
test -f external/bliss/bliss-0.73/graph.hh

py_ver=$($PYTHON -c 'import sys; print("".join(map(str, sys.version_info[:2])))')
nprocs=${CPU_COUNT:-4}
touch $SRC_DIR/.build_start   # marker: only files newer than this are ours

# ---- msys ---------------------------------------------------------------
# `install` alone does not build the C++ test programs; ask for test_hash too.
scons install build/test/test_hash -j $nprocs \
    PREFIX=$PREFIX \
    -D MSYS_WITH_RAPID_JSON=1 \
    -D MSYS_WITH_BLISS=1 \
    -D MSYS_WITH_LPSOLVE=1 \
    PYTHONVER=$py_ver

# ThreeRoe hash sanity check (guards the ARM port of MsysThreeRoe.hpp)
hash=$(build/test/test_hash tests/files/ch4.dms | sed -e 's/tests.*dms //')
test "$hash" = "14718556392828751187"

# ---- viparr -------------------------------------------------------------
pushd viparr
scons install -j $nprocs PREFIX=$PREFIX PYTHONVER=$py_ver
popd

# scons installs python packages into $PREFIX/lib/python; move them to site-packages
mv $PREFIX/lib/python/msys   $SP_DIR/msys
mv $PREFIX/lib/python/viparr $SP_DIR/viparr
rmdir $PREFIX/lib/python

# bliss is linked statically into libmsys; do not ship its archive/headers
# (they would clash with the conda-forge `bliss` package).
rm -f $PREFIX/lib/libbliss.a
rm -rf $PREFIX/include/bliss

# msys/viparr compile with -g. On Linux the DWARF sections end up inside the
# shared objects (60 MB _msys.so); strip them. macOS keeps debug info in
# separate dSYM files, so nothing to do there.
if [ "$(uname)" = Linux ]; then
    for f in $(find $PREFIX/lib $SP_DIR/msys $SP_DIR/viparr -type f -newer $SRC_DIR/.build_start \( -name '*.so' -o -name '*.so.*' \)) \
             $(find $PREFIX/bin -type f -newer $SRC_DIR/.build_start); do
        if head -c 4 "$f" | grep -q 'ELF'; then
            ${STRIP:-strip} --strip-debug "$f"
        fi
    done
fi

# The scons-installed python scripts use '#!/usr/bin/env python', which picks
# whatever python is first on PATH. Point them at this environment's python
# (rattler-build records the prefix and relocates it at install time) so that
# e.g. /path/to/env/bin/dms-info works without activating the environment.
for f in $(find $PREFIX/bin -type f -newer $SRC_DIR/.build_start); do
    if head -c 21 "$f" | grep -q '^#!/usr/bin/env python'; then
        sed -i.orig "1s|^#!/usr/bin/env python.*|#!$PREFIX/bin/python|" "$f"
        rm -f "$f.orig"
    fi
done
