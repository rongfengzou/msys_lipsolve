#!/bin/bash
# usage: verify_linux.sh <python-version>  (run on volc)
set -e
PV=$1; B=/vepfs/Baymax/rongfeng/msys_viparr_build; V=$B/linux_verify
ENV=/vepfs/Baymax/rongfeng/conda_envs/msys_verify_${PV//./}
MIRROR=https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge
conda env remove -y -p $ENV >/dev/null 2>&1 || true
conda create -y -q -p $ENV -c $B/output/channel -c $MIRROR --override-channels msys_viparr python=$PV > $V/create_$PV.log 2>&1
echo "env created: $ENV"
ls $ENV/conda-meta | grep -E "^(msys_viparr|numpy|libboost|lp_solve|python-3|rdkit)-" | sed 's/\.json$//'
echo "libboost pkgs in env: $(ls $ENV/conda-meta | grep -c '^libboost')"
echo "--- ldd libmsys ---"
ldd $ENV/lib/libmsys.so | grep -E "boost|lpsolve|sqlite|libz|not found" || true
echo "--- import + checks ---"
cd $V && env -u PYTHONPATH $ENV/bin/python - <<'PY'
import numpy, msys, viparr, msys.molfile, msys.pfx
print("numpy", numpy.__version__, "msys", msys.version.version, "viparr", viparr.version.version)
s = msys.FromSmilesString("CC"); msys.AssignBondOrderAndFormalCharge(s); print("lpsolve OK")
j = msys.Load("msys_tests/files/jandor-bad.sdf"); msys.AssignBondOrderAndFormalCharge(j)
print("jandor charges", sorted(a.formal_charge for a in j.atoms if a.formal_charge))
print("positions", msys.FromSmilesString("O").positions.shape)
print("rdkit", msys.ConvertToRdkit(s).GetNumAtoms())
PY
echo "--- stk cache write (gzip on linux) + read back ---"
cd $V/msys_tests && rm -f files/.relative.stk.cache.0008
for i in 1 2; do DESRES_LOCATION=1 DTRPLUGIN_VERBOSE=1 env -u PYTHONPATH $ENV/bin/python -c "import msys.molfile as mf; r=mf.DtrReader('files/relative.stk'); print('nframes', r.nframes)" 2>&1 | grep -iE "cache (update|file)|found v8|nframes|fail" | head -4; done
file files/.relative.stk.cache.0008 | sed 's/.*: //'
echo "--- CLI by absolute path, env NOT activated ---"
head -1 $ENV/bin/dms-info; $ENV/bin/dms-version -h | head -1; $ENV/bin/viparr -h 2>&1 | head -1
echo "--- viparr smoke test ---"
env -u PYTHONPATH $ENV/bin/python $V/viparr_smoke.py $V/viparr 2>&1 | tail -1
