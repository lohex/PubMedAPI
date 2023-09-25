from setuptools import setup, find_packages

# Abhängigkeiten aus der requirements.txt Datei lesen
with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()

setup(
    name='PubMedApi',
    version='1.0',
    packages=find_packages(),
    install_requires=requirements,
)