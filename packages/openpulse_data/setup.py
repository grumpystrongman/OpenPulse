from setuptools import find_packages, setup

setup(
    name="openpulse-data",
    version="0.1.0",
    description="OpenPulse data platform access helpers",
    packages=find_packages(),
    install_requires=["clickhouse-connect>=0.8.6", "confluent-kafka>=2.5.0", "boto3>=1.35.0", "pydantic-settings>=2.4.0", "tenacity>=9.0.0"],
)
