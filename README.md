# msys_viparr — conda package of msys + viparr + lpsolve on a current toolchain

One conda package that bundles

| component | version | source |
|-----------|---------|--------|
| msys      | 1.7.359 | github.com/DEShawResearch/msys @ `30aa5b6f` (master, 2025-12-05) |
| viparr    | 4.7.35  | github.com/DEShawResearch/viparr @ `d0c869df` (master) |
| lpsolve   | 5.5.2.11 | conda-forge `lp_solve` (bond order / formal charge assignment) |
| bliss     | 0.73    | tcs.hut.fi, linked statically into libmsys (resonant charge acceleration) |
| rapidjson | conda-forge | fast JSON import/export |
| xtc reader | — | dp.tech gromacs xtc patch carried over from the old recipe |

It replaces the old `ye-ding::msys_viparr 1.7.359 py310h70deae4_3`, which was
pinned to **python 3.10, numpy < 2 and libboost 1.84**, and whose source
tarballs (openfiles.mlops.dp.tech) no longer exist. The patched sources of
msys, viparr and bliss are vendored in this repository (`msys/`, `viparr/`,
`bliss-0.73/`), so the package builds without any external source host,
against whatever boost / numpy / pybind11 conda-forge currently ships, for
python 3.10 – 3.13.

## Built packages (in `output/channel/`)

| subdir | python | file |
|--------|--------|------|
| osx-arm64 | 3.10 | `msys_viparr-1.7.359-py310hbd7d6ef_1.conda` |
| osx-arm64 | 3.11 | `msys_viparr-1.7.359-py311h5f8ada8_1.conda` |
| osx-arm64 | 3.12 | `msys_viparr-1.7.359-py312h440f24a_1.conda` |
| osx-arm64 | 3.13 | `msys_viparr-1.7.359-py313h7e60211_1.conda` |
| linux-64  | 3.10 | `msys_viparr-1.7.359-py310h8e7c8fa_1.conda` |
| linux-64  | 3.11 | `msys_viparr-1.7.359-py311h48b7412_1.conda` |
| linux-64  | 3.12 | `msys_viparr-1.7.359-py312h738df08_1.conda` |
| linux-64  | 3.13 | `msys_viparr-1.7.359-py313hf70daa8_1.conda` |

Each is about 3–4 MB. All eight passed the recipe's tests. Build number 1
(`_1`) is the build with the kekulized SDF export (see below) and the
`run_constraints` entry that stops conda from installing it next to the old
`msys_viparr_lpsolve55` package, which ships the same files. The `_0`
builds were withdrawn. Fresh-env checks (see Validation) were done on both
platforms.

## Install

```bash
# from the local channel produced by ./build_all.sh
conda create -n msys -c /Users/zourongfeng/code_del/msys_lipsolve/output/channel -c conda-forge \
    msys_viparr python=3.12        # or 3.10 / 3.11 / 3.13
conda activate msys
python -c "import msys, viparr; print(msys.version.version, viparr.version.version)"
```

Run-time dependencies are only `python`, `numpy`, `lp_solve 5.5.*`,
`libsqlite`, `zlib` and `rdkit` (for `msys.ConvertToRdkit`). **There is no
run-time boost dependency at all**: boost is used header-only at build time,
so this package never conflicts with whichever `libboost` version rdkit (or
anything else) is pinned to. Any numpy ≥ 1.x works at run time because the
extension is compiled against numpy 2 headers.

To share the package, upload the `.conda` files in `output/channel/osx-arm64/`
to an anaconda.org channel (`rattler-build upload anaconda ...`) or copy the
channel directory.

## Build

```bash
# build env (once; the `msysbuild` env on this machine already has it)
conda create -n msysbuild -c conda-forge rattler-build
conda activate msysbuild

./build_all.sh          # all python versions in recipe/variants.yaml
./build_all.sh 3.12     # one variant
```

Output goes to `output/channel`; the build log of each run is printed by
rattler-build. The sources are the vendored trees (`path:` sources in the
recipe); only the conda build/host dependencies are downloaded.

### Linux

The linux-64 packages were built with the same recipe on the `volc` host
(ssh alias; x86_64, conda 25.7) in `/vepfs/Baymax/rongfeng/msys_viparr_build`,
using the TUNA conda-forge mirror (8 MB/s there, vs 0.4 MB/s from upstream):

```bash
ssh volc
export PATH=/vepfs/Baymax/rongfeng/conda_envs/rattler-build/bin:$PATH
cd /vepfs/Baymax/rongfeng/msys_viparr_build
CHANNEL=https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge ./build_all.sh   # ~12 min for 4 variants
```

The resulting `output/channel/linux-64/` was copied back into this
repository's channel, so the local channel serves both platforms. The only
Linux-specific build step is `build.sh` stripping debug sections from the
ELF shared objects: msys compiles with `-g`, and on Linux the DWARF data
ends up inside the `.so` files (the unstripped `_msys` extension was 61 MB
and the package 59 MB; stripped, the package is 3.7 MB).

## Layout

```
msys/                msys 1.7.359 source tree, patched (SConstruct, src/, python/, tools/, tests/)
viparr/              viparr 4.7.35 source tree, patched
bliss-0.73/          bliss 0.73 (linked statically into libmsys; copied to msys/external/bliss/bliss-0.73 at build time)
recipe/
  recipe.yaml        rattler-build v1 recipe (path sources, deps, tests)
  variants.yaml      python versions to build
  build.sh           scons build of msys, then viparr; moves python pkgs to site-packages
  patches/           record of the changes applied to the upstream trees (NOT applied by the recipe)
    msys-0001-arm-py312-bliss-xtc.patch   legacy dp.tech patch: ARM (no SSE), py3.12,
                                          bliss SConscript, gromacs xtc reader, test fixes
    msys-0002-modern-toolchain.patch      new, see below
    viparr-0001-build-py310plus.patch     legacy: python-version parsing, toolchain env,
                                          missing <cassert>
    viparr-0002-pythonver-313.patch       new: allow PYTHONVER 313/314
    msys-0003-kekulize-sdf-export.patch   SDF export writes Kekule bond orders, never type 4
                                          (behaviour of the old dp.tech package, see below)
build_all.sh         driver around rattler-build
linux_verify/        parity / verification scripts used on the Linux host
  parity.py          34 general probes, old vs new package
  fepfixer_probe.py  Load / SaveDMS / GuessHydrogenPositions / Graph.match /
                     findContactIds / SDF export probes (the calls fepfixer uses)
```

Edit the code directly in `msys/` and `viparr/`; the recipe copies these
directories into its work dir (honouring their `.gitignore`, so a stray
`build/` is not picked up) and runs `recipe/build.sh` there.

## Source provenance

The vendored trees are exactly the upstream archives below with the patches
in `recipe/patches/` applied (`patch -p1`, in the listed order):

| tree | archive | sha256 |
|------|---------|--------|
| `msys/` | `https://github.com/DEShawResearch/msys/archive/30aa5b6f2c4521e4081281e4210cae6d92bd5f19.tar.gz` | `c6b766a54583f518c2620797a257b638f78b361178b8a58f1285eec6b517d7f7` |
| `viparr/` | `https://github.com/DEShawResearch/viparr/archive/d0c869df9a44e1fdaf5f1ce44646178c30cff6e5.tar.gz` | `61c65182dc677d9db2399585ee108e1835563fd100491afa5b58a84272c02f28` |
| `bliss-0.73/` | `http://www.tcs.hut.fi/Software/bliss/bliss-0.73.zip` (unpatched) | `f57bf32804140cad58b1240b804e0dbd68f7e6bf67eba8e0c0fa3a62fd7f0f84` |

To see what differs from upstream today, diff against a fresh extraction of
the archive; the patch files are a snapshot of that diff as of the import
and are not maintained once the trees are edited in place.

## What `msys-0002-modern-toolchain.patch` changed and why

* **numpy 2** — `python/numpy_compat.hxx` (new) restores the pre-1.7 flag
  aliases (`NPY_FORCECAST`, `NPY_C_CONTIGUOUS`, `NPY_ALIGNED`,
  `NPY_INOUT_ARRAY`) and adds `PyObject*` overloads of
  `PyArray_DIM/DATA/TYPE/NDIM`, which numpy 2 only provides for
  `PyArrayObject*`. msys passes `PyObject*` at ~60 call sites; the shim avoids
  touching them. Included after the numpy header in `pfx.cxx`, `system.cxx`
  and the three `molfile/*.cxx` files. Guarded by `NPY_ABI_VERSION >= 2`, so
  the same source still builds against numpy 1.
* **no boost at run time** — msys used two compiled boost libraries:
  `boost_filesystem` and `boost_iostreams` (the gzip filter), both only in
  `src/molfile/dtrplugin.cxx` (stk file handling and its on-disk cache).
  They are replaced by POSIX calls (`lstat`/`readlink`, `mkstemp`, `rename`)
  and by msys's own zlib-based `compression.hxx` streams, which already
  auto-detect gzip. `src/SConscript` links no `boost_*` library any more
  (`boost_system` has been header-only since 1.69 anyway), and the unused
  `<boost/filesystem.hpp>` include in `tools/bin/mae2dms.cxx` is dropped.
  The remaining boost use (spirit/qi, fusion, optional, tuple, numeric cast,
  iostreams array device) is header-only, so the recipe depends on
  `libboost-headers` in `host` only and exports no `libboost` run pin.
  Verified: relative stk paths resolve, the stk cache is written and read
  back (`DESRES_LOCATION=1 DTRPLUGIN_VERBOSE=1`), and `otool -L libmsys.dylib`
  shows only sqlite3, zlib, lpsolve55 and libc++.
* **newer libc++** — `#include <iterator>` for `std::back_inserter`
  (`src/pfx/pfx.hxx`, `src/mol2/export.cxx`, five `tests/*.cxx`) and
  `<cstdlib>/<cmath>` for `std::abs` in the xtc reader (`src/molfile/gromacs.h`).
* **bliss** — built as a static archive and linked into `libmsys`, so the
  package ships no `libbliss.dylib` / `include/bliss` that would clash with
  the conda-forge `bliss` package.
* `external/sconsutils.py` — PYTHONVER list extended to 313 / 314.

## SDF export of aromatic bonds (`msys-0003-kekulize-sdf-export.patch`)

Upstream `src/sdf/export.cxx` writes bond type 4 for any bond whose
`aromatic` flag is set (bonds read from a type-4 SDF, and every aromatic bond
of a `FromSmilesString` molecule), even after `AssignBondOrderAndFormalCharge`
has assigned Kekule orders. The old dp.tech package carried a one-line patch
(`patch_kekulize_sdf`, tag `msys_viparr/v1.7.359.0_t2` of conda_recipes)
that writes `bnd.order` instead, so its SDF output is always kekulized.
`linux_verify/fepfixer_probe.py` caught the difference (phenol from SMILES:
old `1 2 1 2 1 1 2 ...`, unpatched new `4 4 4 4 4 1 4 ...`); this build
applies the same change. Consequence: a type-4 SDF loaded and saved
*without* calling `AssignBondOrderAndFormalCharge` comes out with all
single bonds, exactly as in the old package.

`build.sh` adds `-I$PREFIX/include/lpsolve` instead of symlinking
`include/lp_solve` into the package (msys already falls back to `<lp_lib.h>`),
builds and runs `test_hash` (ThreeRoe hash check), and rewrites the
`#!/usr/bin/env python` shebang of the installed `dms-*` / `viparr*` scripts
to the environment's own python, so `/path/to/env/bin/dms-info` works without
activating the environment (the old package picked whatever `python` was on
PATH).

## Validation

### linux-64 (fresh envs from the channel, python 3.10 and 3.12, numpy 2.2 / 2.5, rdkit 2026.09)

* Installs beside conda-forge rdkit (boost 1.90) with no conflict;
  `ldd libmsys.so` shows only sqlite3, zlib, lpsolve55.
* imports, lpsolve bond-order assignment (jandor-bad.sdf gives +1 / −1),
  `positions` under numpy 2, `ConvertToRdkit`, CLI scripts by absolute path
  without activation, viparr `testViparrParametrizeFragment`: all pass.
* The stk cache round-trip (`DESRES_LOCATION=1`) writes a gzip-compressed
  cache file and reads it back. This is the one code path that differs from
  macOS, since the boost gzip filter it replaces was only active on Linux.

### Rebuild from the vendored trees

After the sources were vendored (recipe `path:` sources instead of archive
URLs + patches), the osx-arm64 python 3.12 package was rebuilt and compared
file by file with the one built from the archives: same 242 files, 184
byte-identical. The other 58 are the installed scripts (differ only in the
build-prefix shebang that conda relocates at install time) and the Mach-O
binaries, whose `__TEXT`, `__DATA_CONST` and `__DATA` segments are
byte-identical; only `LC_UUID`, the code signature and the debug stab entries
(`.o` paths and mtimes in `__LINKEDIT`) differ. The recipe tests passed.

### Parity with the package already deployed on `volc`

The envs on `volc` (`fep_166`, `atom_mapper`, `fepfixer*`, ...) use
`msys_viparr_lpsolve55 1.7.359 py310h1eb418a_4` from the internal quetz
channel `baymax` (Jan 2025). It is the same msys/viparr source version but
pinned to python 3.10, numpy < 2 and one exact `libboost 1.86.0` build.
`linux_verify/parity.py` (34 probes on identical inputs) was run in
`fep_166` and in a fresh python 3.10 env from this channel:

* 33 of 34 results identical; the only difference is the python patch
  level (3.10.20 vs 3.10.22).
* Identical: msys/viparr versions, lpsolve formal charges and bond orders on
  jandor-bad.sdf, atom-selection counts on ww.dms (7 queries), position
  hashes before/after a DMS round trip, aromaticity/SSSR/SMARTS counts,
  mae and multi-SDF loading, `pfx.aligned_rmsd` rotation and rmsd, dtr frame
  coordinates, rdkit SMILES, and the full viparr parametrization of ww.dms
  with amber99 + tip4p (11 tables with identical term counts, identical
  per-atom charge hash, identical stretch parameters, 46 nonbonded params).
* Same feature set: lpsolve yes, InChI no, in both.
* `linux_verify/fepfixer_probe.py` (21 probes: `Load` of dms/sdf/mae,
  `SaveDMS` round trip with per-table param/term hashes,
  `GuessHydrogenPositions`, `Graph.match`/`matchAll`/`hash`,
  `findContactIds` with ids/other/pos/ignore_excluded, SDF export) in the
  `fepfixer` env (old package, numpy 1.26.4) vs two fresh python 3.10 envs
  from the `_1` packages, one with numpy 2.2.6 and one with numpy 1.26.4:
  21/21 identical with numpy 1.26.4, 20/21 with numpy 2 (the numpy version
  string is the only difference). `parity.py` in the same envs: identical
  apart from the python patch level (3.10.20 vs 3.10.22) and numpy version.
  Before `msys-0003` the SDF bond types of aromatic bonds differed (see
  above).

### osx-arm64 (python 3.12, numpy 2.5.4, boost headers 1.90/1.92, pybind11 3.1)

* The built `.conda` installs into a fresh env next to conda-forge
  `rdkit 2026.09.1` (which pins `libboost 1.90`) with no conflict, and
  `otool -L libmsys.dylib` there shows only sqlite3, zlib, lpsolve55, libc++.
* `import msys, viparr, msys.molfile, msys.pfx` under numpy 2.
* lpsolve: `AssignBondOrderAndFormalCharge` on `jandor-bad.sdf` gives the
  expected +1 / −1 formal charges.
* ThreeRoe hash of `tests/files/ch4.dms` = `14718556392828751187` (ARM port).
* `pfx.aligned_rmsd` results bit-identical to the old numpy-1 package.
* viparr `testViparrParametrizeFragment` (amber99 + tip4p on ww.dms) passes.
* `tests/test_ut.py` (msys): 243 passed / 10 failed. The old package fails
  the same 10 plus 5 more. The 10 are: InChI (×4) and cereal (×2) not built,
  lz4/zstd compression (×2) not built, `testLoadDmsMany`, `testMemoryLeakPosVel`
  (Linux `/proc` parsing) — all identical in the old package.
* viparr `test/python_tests.py`: 11 failed / 9 passed, every failure also
  fails in the old package (upstream test rot such as
  `Forcefield.PluginRegistry` no longer being exported); the new build
  additionally passes `testViparrSolvate`.

## Known limitations (all pre-existing in the old package)

* `viparr.ExportForcefield` aborts (SIGABRT inside dyld) on macOS, in both the
  old and this build; import/parametrize paths are unaffected.
* InChI, cereal, lz4 and zstd support are not compiled in (same as before).
  Enabling lz4/zstd would only need `lz4-c`, `zstd` in host and
  `MSYS_WITH_LZ4=1 MSYS_WITH_ZSTD=1` on the scons line.
* `viparr-rigidify` imports scipy, which is not a declared dependency.
* Forcefield data is not included; set `VIPARR_FFPATH` to the `ff` dir of a
  `viparr-ffpublic` checkout.
