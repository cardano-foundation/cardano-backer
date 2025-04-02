from setuptools import setup, find_packages
from os.path import splitext
from os.path import basename
from glob import glob


setup(
    name='backer',
    version='0.1',
    license='Apache Software License 2.0',
    description='KERI Cardano Registrar Backer',
    long_description="KERI witness/backer that anchors Key Event on Cardano blockchain",
    author='RootsID',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    entry_points={
        'console_scripts': [
            'backer = backer.cli.backer:main',
        ]
    },
    python_requires='>=3.12.0',
    install_requires=[
        'hio==0.6.17',
        'keri==1.2.2',
        'multicommand>=1.0.0',
        'pycardano==0.13.0',
        'pprintpp>=0.4.0',
        'ogmios>=1.3.0'
    ]
    )
