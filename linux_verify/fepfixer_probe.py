# Same-input probe of the msys calls fepfixer uses (Load, SaveDMS,
# GuessHydrogenPositions, Graph.match, System.findContactIds) plus SDF export
# of aromatic bonds. Prints one JSON dict. Run from linux_verify/.
import sys, json, tempfile, hashlib
import numpy as np
import msys

out = {}


def probe(name, fn):
    try:
        out[name] = fn()
    except Exception as e:
        out[name] = "ERR: " + str(e).splitlines()[0][:100]


def h(a):
    return hashlib.md5(np.ascontiguousarray(np.round(np.asarray(a, dtype=float), 4)).tobytes()).hexdigest()[:12]


def hs(x):
    return hashlib.md5(str(x).encode()).hexdigest()[:12]


def table_sig(t):
    params = [[p[k] for k in t.params.props] for p in t.params.params]
    terms = [[a.id for a in term.atoms] + [term.param.id if term.param is not None else -1] for term in t.terms]
    return [t.name, t.nterms, t.params.nparams, hs(params), hs(terms)]


out["python"] = ".".join(map(str, sys.version_info[:3]))
out["numpy"] = np.__version__
out["msys_version"] = msys.version.version
tmp = tempfile.mkdtemp()

# ---- Load
w = msys.Load("viparr/test/dms/ww.dms")
probe("load_ww", lambda: [w.natoms, w.nbonds, w.nresidues, w.nchains, sorted(t.name for t in w.tables), h(w.positions), h(w.cell), sorted(table_sig(t) for t in w.tables)])
j = msys.Load("msys_tests/files/jandor-bad.sdf")
probe("load_sdf", lambda: [j.natoms, j.nbonds, [b.order for b in j.bonds], [a.formal_charge for a in j.atoms], h(j.positions)])
probe("load_sdf_many", lambda: [(m.natoms, m.nbonds) for m in msys.LoadMany("msys_tests/files/cofactors.sdf")])
probe("load_mae", lambda: (lambda m: [m.natoms, m.nbonds, sorted(t.name for t in m.tables), h(m.positions)])(msys.Load("msys_tests/files/two.mae")))
probe("load_structure_only", lambda: (lambda m: [m.natoms, m.nbonds, len(m.tables), h(m.positions)])(msys.Load("viparr/test/dms/ww.dms", structure_only=True)))
probe("load_without_tables", lambda: (lambda m: [m.natoms, sorted(t.name for t in m.tables)])(msys.Load("viparr/test/dms/ww.dms", without_tables=True)))


# ---- SaveDMS round trip
def savedms():
    p = tmp + "/ww_out.dms"
    msys.SaveDMS(w, p)
    r = msys.Load(p)
    p2 = tmp + "/ww_so.dms"
    msys.SaveDMS(w, p2, structure_only=True)
    r2 = msys.Load(p2)
    return [r.natoms, r.nbonds, r.nresidues, h(r.positions), h(r.cell), sorted(table_sig(t) for t in r.tables),
            [a.name for a in r.atoms][:12], [(a.charge, a.mass) for a in r.atoms][:5],
            r2.natoms, len(r2.tables), h(r2.positions)]


probe("savedms_roundtrip", savedms)


# ---- GuessHydrogenPositions
def guessh(path, nmax):
    m = msys.Load(path, structure_only=True)
    hyd = [a for a in m.atoms if a.atomic_number == 1][:nmax]
    for a in hyd:
        a.pos = [0.0, 0.0, 0.0]
    msys.GuessHydrogenPositions(hyd)
    d = [float(np.linalg.norm(a.pos - a.bonded_atoms[0].pos)) for a in hyd]
    return [len(hyd), h(m.positions), round(min(d), 4), round(max(d), 4), [round(x, 4) for x in d[:6]]]


probe("guessh_ww", lambda: guessh("viparr/test/dms/ww.dms", 60))
probe("guessh_jandor", lambda: guessh("msys_tests/files/jandor-bad.sdf", 100))


# ---- Graph.match
def graph_match():
    a = msys.Load("msys_tests/files/jandor-bad.sdf")
    b = msys.Load("msys_tests/files/jandor-bad.sdf")
    msys.AssignBondOrderAndFormalCharge(a)
    msys.AssignBondOrderAndFormalCharge(b)
    g1, g2 = msys.Graph(a), msys.Graph(b)
    mp = g1.match(g2)
    pairs = sorted((x.id, y.id) for x, y in mp.items()) if mp else None
    res = [pairs is not None, len(pairs) if pairs else 0, pairs[:8], hs(pairs)]
    res.append(g1.match(msys.Graph(msys.FromSmilesString("CCO"))) is None)
    res.append(len(g1.matchAll(g2)))
    frags = w.updateFragids()
    gs = [msys.Graph(f) for f in frags[:4]]
    res.append([[gi.match(gj) is not None for gj in gs] for gi in gs])
    res.append(sorted(set(msys.Graph(f).hash() for f in frags)))
    return res


probe("graph_match", graph_match)


# ---- findContactIds
def contacts():
    c = sorted((i, j, round(d, 4)) for i, j, d in w.findContactIds(3.0))
    ids = list(range(100))
    other = list(range(100, w.natoms))
    c2 = sorted((i, j, round(d, 4)) for i, j, d in w.findContactIds(4.0, ids=ids, other=other))
    c3 = sorted((i, j, round(d, 4)) for i, j, d in w.findContactIds(3.0, ignore_excluded=True))
    c4 = sorted((i, j, round(d, 4)) for i, j, d in w.findContactIds(3.0, pos=w.positions))
    c5 = sorted((i, j, round(d, 4)) for i, j, d in w.findContactIds(3.5, ids=ids))
    return [len(c), c[:5], hs(c), len(c2), c2[:3], hs(c2), len(c3), hs(c3), c4 == c, len(c5), hs(c5)]


probe("find_contact_ids", contacts)


# ---- SDF export of aromatic bonds (kekulized orders vs type 4)
def sdf_bond_block(m):
    p = tmp + "/arom.sdf"
    msys.Save(m, p)
    lines = open(p).read().splitlines()
    na, nb = int(lines[3][:3]), int(lines[3][3:6])
    bonds = lines[4 + na:4 + na + nb]
    types = [int(l[6:9]) for l in bonds]
    return {"system_orders": [b.order for b in m.bonds], "sdf_bond_types": types, "has_type4": 4 in types, "block_md5": hs(bonds)}


def sdf_smiles(smi):
    m = msys.FromSmilesString(smi)
    msys.AssignBondOrderAndFormalCharge(m)
    return sdf_bond_block(m)


probe("sdf_export_phenol", lambda: sdf_smiles("c1ccccc1O"))
probe("sdf_export_indole", lambda: sdf_smiles("c1ccc2[nH]ccc2c1"))
probe("sdf_export_jandor", lambda: (lambda m: (msys.AssignBondOrderAndFormalCharge(m), sdf_bond_block(m))[1])(msys.Load("msys_tests/files/jandor-bad.sdf")))
probe("sdf_export_jandor_as_loaded", lambda: sdf_bond_block(msys.Load("msys_tests/files/jandor-bad.sdf")))
probe("sdf_format_phenol", lambda: hs(msys.FormatSDF((lambda m: (msys.AssignBondOrderAndFormalCharge(m), m)[1])(msys.FromSmilesString("c1ccccc1O")))))


# ---- SDF input with aromatic bond type 4 (benzene with explicit H): does the
# exporter write type 4 back, or kekulized orders? (patch_kekulize_sdf question)
def type4_benzene_sdf():
    import math
    atoms, bonds = [], []
    for k in range(6):
        a = math.radians(60 * k)
        atoms.append(("C", 1.40 * math.cos(a), 1.40 * math.sin(a)))
        atoms.append(("H", 2.48 * math.cos(a), 2.48 * math.sin(a)))
    for k in range(6):
        bonds.append((2 * k + 1, 2 * ((k + 1) % 6) + 1, 4))   # C-C aromatic
        bonds.append((2 * k + 1, 2 * k + 2, 1))               # C-H
    lines = ["benzene", "  probe", ""]
    lines.append(f"{len(atoms):3d}{len(bonds):3d}  0  0  0  0  0  0  0  0999 V2000")
    for sym, x, y in atoms:
        lines.append(f"{x:10.4f}{y:10.4f}{0.0:10.4f} {sym:<3} 0  0  0  0  0  0  0  0  0  0  0  0")
    for i, j, t in bonds:
        lines.append(f"{i:3d}{j:3d}{t:3d}  0  0  0  0")
    lines += ["M  END", "$$$$", ""]
    path = tmp + "/benzene_type4.sdf"
    open(path, "w").write("\n".join(lines))
    return path


def sdf_type4(assign):
    m = msys.Load(type4_benzene_sdf())
    if assign:
        msys.AssignBondOrderAndFormalCharge(m)
    r = sdf_bond_block(m)
    r["natoms"] = m.natoms
    r["formal_charges"] = [a.formal_charge for a in m.atoms]
    return r


probe("sdf_type4_as_loaded", lambda: sdf_type4(False))
probe("sdf_type4_after_assign", lambda: sdf_type4(True))

print(json.dumps(out, indent=1, default=str))
