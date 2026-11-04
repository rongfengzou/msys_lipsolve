import tempfile
from pathlib import Path

import numpy

from msys import molfile

_DATA_DIR = Path(__file__).parent / "files"


def test_xtc():
    xtc = molfile.xtc.read(str(_DATA_DIR / "conf.xtc"))
    with tempfile.NamedTemporaryFile(suffix=".xtc") as tmp:
        xtc1 = molfile.xtc.write(tmp.name, natoms=xtc.natoms)
        ref_frame = xtc.next()
        xtc1.frame(xtc.next())
        xtc1.frame(xtc.next())
        xtc1.close()
        r = molfile.xtc.read(tmp.name)
        assert r.natoms == 1200
        n = 0
        for f in r.frames():
            assert numpy.allclose(f.pos, ref_frame.pos)
            n += 1
        assert n == 2


def test_gro():
    gro = molfile.gro.read(str(_DATA_DIR / "conf.gro"))
    ref_frame = molfile.xtc.read(str(_DATA_DIR / "conf.xtc")).next()
    with tempfile.NamedTemporaryFile(suffix=".gro") as tmp:
        gro1 = molfile.gro.write(tmp.name, atoms=gro.atoms, natoms=gro.natoms)
        gro1.frame(ref_frame)
        gro1.close()
        r = molfile.gro.read(tmp.name)
        assert r.natoms == 1200
        box = [[22.93339968, 0., 0.], [0., 22.93339968, 0.],
               [0., 0., 22.93339968]]
        f = r.next()

        assert numpy.allclose(f.box, box)
        assert numpy.allclose(ref_frame.pos, f.pos)
