# Same-input behaviour probe for msys/viparr; prints one JSON dict. Run from linux_verify/.
import sys, json, os, tempfile, hashlib
import numpy as np
out = {}
def probe(name, fn):
    try:
        out[name] = fn()
    except Exception as e:
        out[name] = "ERR: " + str(e).splitlines()[0][:80]
def h(a):
    return hashlib.md5(np.ascontiguousarray(np.round(np.asarray(a, dtype=float), 4)).tobytes()).hexdigest()[:12]
import msys
out["python"] = ".".join(map(str, sys.version_info[:3])); out["numpy"] = np.__version__
out["msys_version"] = msys.version.version
tmp = tempfile.mkdtemp()
s = msys.FromSmilesString("CC")
probe("feat_lpsolve", lambda: (msys.AssignBondOrderAndFormalCharge(s), "yes")[1])
probe("feat_inchi", lambda: msys.InChI(s).string)
m = msys.Load("msys_tests/files/ch4.dms")
for ext in ("gz", "zst", "lz4"):
    probe("feat_" + ext, lambda ext=ext: (msys.Save(m, tmp + "/a.dms." + ext), msys.Load(tmp + "/a.dms." + ext).natoms)[1])
j = msys.Load("msys_tests/files/jandor-bad.sdf"); msys.AssignBondOrderAndFormalCharge(j)
probe("jandor_charges", lambda: sorted(a.formal_charge for a in j.atoms if a.formal_charge))
probe("jandor_bond_order_hist", lambda: {int(o): sum(1 for b in j.bonds if b.order == o) for o in sorted(set(b.order for b in j.bonds))})
w = msys.Load("viparr/test/dms/ww.dms", structure_only=True)
probe("ww_counts", lambda: [w.natoms, w.nbonds, w.nresidues, w.nchains])
for q in ["protein", "water", "name CA", "backbone", "resid 10 to 20 and not hydrogen", "within 4 of resname TRP", "same residue as (within 3 of water and protein)"]:
    probe("ww_sel[" + q + "]", lambda q=q: len(w.selectIds(q)))
probe("ww_pos_hash", lambda: h(w.positions))
def rt():
    msys.Save(w, tmp + "/ww2.dms"); w2 = msys.Load(tmp + "/ww2.dms"); return [w2.natoms, h(w2.positions)]
probe("ww_roundtrip", rt)
ann = msys.AnnotatedSystem(j)
probe("jandor_aromatic_atoms", lambda: sum(1 for a in j.atoms if ann.aromatic(a)))
probe("jandor_sssr", lambda: len(msys.GetSSSR(j, j.atoms)))
probe("jandor_smarts_cN", lambda: len(msys.SmartsPattern("[c][#7]").findMatches(ann)))
probe("two_mae", lambda: (lambda mae: [mae.natoms, len(mae.tables), sorted(t.name for t in mae.tables)[:6]])(msys.Load("msys_tests/files/two.mae")))
probe("cofactors_sdf", lambda: (lambda c: [len(c), sum(x.natoms for x in c if x)])([x for x in msys.LoadMany("msys_tests/files/cofactors.sdf")]))
def pf():
    import msys.pfx as pfx
    np.random.seed(0); X = np.random.rand(20, 3); Y = X + 0.1 * np.random.rand(20, 3)
    R, rms = pfx.aligned_rmsd(X, Y); return [round(float(rms), 6), h(R)]
probe("pfx_aligned_rmsd", pf)
def dtr():
    import msys.molfile as mf
    r = mf.DtrReader("msys_tests/files/relative.stk"); f0 = r.frame(0); return [r.nframes, int(r.natoms), h(f0.pos)]
probe("dtr_frame0", dtr)
def rd():
    from rdkit import Chem
    return Chem.MolToSmiles(msys.ConvertToRdkit(j))
probe("rdkit_smiles", rd)
def vp():
    import viparr
    out["viparr_version"] = viparr.version.version
    viparr.Forcefield.ClearParamTables()
    amber = viparr.ImportForcefield("viparr/test/ff3/amber99"); tip = viparr.ImportForcefield("viparr/test/ff3/tip4p")
    v = msys.Load("viparr/test/dms/ww.dms", structure_only=True)
    viparr.ExecuteViparr(v, [amber, tip], verbose=False)
    out["viparr_tables"] = {t.name: t.nterms for t in v.tables}
    out["viparr_total_charge"] = round(sum(a.charge for a in v.atoms), 4)
    out["viparr_charge_hash"] = h([a.charge for a in v.atoms])
    out["viparr_stretch_params_hash"] = h([[p["fc"], p["r0"]] for p in v.table("stretch_harm").params.params])
    return v.table("nonbonded").params.nparams
probe("viparr_nb_params", vp)
print(json.dumps(out, indent=1, sort_keys=True))
