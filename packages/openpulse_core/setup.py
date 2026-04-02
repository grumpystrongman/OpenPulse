from setuptools import find_packages, setup

setup(
    name="openpulse-core",
    version="0.1.0",
    description="OpenPulse core schemas, mappings, and simulators",
    packages=find_packages(),
    install_requires=["pydantic>=2.8.0", "orjson>=3.10.0", "python-dateutil>=2.9.0"],
)
