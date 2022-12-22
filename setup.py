from __future__ import print_function
from setuptools import setup, Command
import os, sys

NAME="flange"
with open(os.path.join("flange", "version.py")) as f:
    code = compile(f.read(), "version.py", "exec")
    exec(code)

sys.path.append(".")
if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    print("------------------------------")
    print("Must use python 3.5 or greater", file=sys.stderr)
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
    name=NAME,
    version=__version__,
    package_data={
        'admin': ['public/*', 'public/js/*.js', 'public/css/*.css']
    },
    packages=["flange", "flange.tools", "flange.passes", "flange.resolvers",
              "flanged", "flanged.handlers", "flanged.tests", "admin"],
    author="Joseph Cottam, Jeremy Musser",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    
    dependency_links=[
        "git+https://github.com/periscope-ps/lace.git/@master#egg=lace",
        "git+https://github.com/periscope-ps/unisrt.git/@develop#egg=unisrt",
    ],
    install_requires=[
        "falcon>=1.3.0",
        "bson",
        "configparser",
        "unisrt",
        "lace",
        "requests",
        "tornado",
        "graphviz"
    ],
    entry_points = {
        'console_scripts': [
            'flange = flange.compiler:main',
            'flanged = flanged.app:main',
            'fladmin = admin.app:main',
        ]
    },
    cmdclass={'test': tester },
)
