from setuptools import setup, find_packages
import pathlib

VERSION = "0.2.0"


def load_requirements():
    requirements = []
    REQS_PATH = pathlib.Path(__file__).resolve().parent.joinpath('requirements.txt')
    if REQS_PATH.exists() and REQS_PATH.is_file():
        requirements = [x for x in REQS_PATH.read_text().splitlines() if (len(x) and not x.startswith("#"))]
    return requirements


setup(
    name="nornir_inventory_rancid",
    packages=find_packages(),
    version=VERSION,
    author="James Cornman <http://github.com/jizaymes>",
    description="RANCID Inventory for Nornir",
    install_requires=load_requirements(),
    include_package_data=True
)
