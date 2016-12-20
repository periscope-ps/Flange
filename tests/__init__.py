

def test(case=None):
    "Run tests by name...helpful in jupyter notebook"
    import sys

    unis._runtime_cache = {}
    print("Cleared unis Runtime cache")

    if case is None:
        module = sys.modules[__name__]
        suite = unittest.TestLoader().loadTestsFromModule(module)
    else:
        suite = unittest.TestLoader().loadTestsFromTestCase(case)
    unittest.TextTestRunner().run(suite)

