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
    packages=["flange", "flange.primitives", "flange.backend", "flanged", "flanged.handlers", "flanged.tests"],
    author="Joseph Cottam, Jeremy Musser",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    
    dependency_links=[
        "git+https://github.com/periscope-ps/lace.git/@master#egg=lace",
        "git+https://github.com/periscope-ps/unisrt.git/@develop#egg=unisrt",
    ],
    install_requires=[
        "falcon",
        "bson",
    ],
    entry_points = {
        'console_scripts': [
            'flange = flange.compiler:main',
            'flanged = flanged.app:main'
        ]
    },
    cmdclass={'test': tester },
)
