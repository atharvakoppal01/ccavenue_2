from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

# get version from __version__ variable in custom_app/__init__.py
from custom_app import __version__ as version

setup(
    name="custom_app",
    version=version,
    description="Custom ERPNext App with CCAvenue Integration",
    author="LMC",
    author_email="lmc@gmail.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)