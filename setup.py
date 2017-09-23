from __future__ import print_function
from setuptools import setup, Command
import os

import sys

version = "0.1.dev0"

sys.path.append(".")
if sys.version_info[0] < 3:
    print("------------------------------")
    print("Must use python 3.0 or greater", file=sys.stderr)
    print("Found python verion ", sys.version_info, file=sys.stderr)
    print("Installation aborted", file=sys.stderr)
    print("------------------------------")
    sys.exit()

class tester(Command):
    description = "Run unittests for Flanged"
    user_options = []
    
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    def run(self):
        import flanged.test.runtests as tests
        return tests.main()

setup(
    name="flanged",
    version=version,
    packages=["flange", "flange.backend", "flanged", "flanged.handlers", "flanged.tests"],
    author="Joseph Cottam, Jeremy Musser",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    
    install_requires=[
        "falcon",
        "bson",
    ],
    cmdclass={'test': tester },
)
