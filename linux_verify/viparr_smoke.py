# run TestMain.testViparrParametrizeFragment from viparr/test/python_tests.py without pytest
import importlib.util, unittest, os, sys
spec = importlib.util.spec_from_file_location("vp_tests", os.path.join(sys.argv[1], "test", "python_tests.py"))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
os.chdir(sys.argv[1])
suite = unittest.TestSuite([mod.TestMain("testViparrParametrizeFragment")])
r = unittest.TextTestRunner(verbosity=0).run(suite)
print("viparr smoke test:", "PASS" if r.wasSuccessful() else "FAIL")
