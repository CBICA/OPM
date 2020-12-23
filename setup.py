from setuptools import setup, find_packages

with open('README.md') as readme_file:
  readme = readme_file.read()

requirements = [
    'openslide-python',
    'scikit-image',
    'matplotlib',
    'numpy',
    'tqdm',
    'pandas',
    'wheel',
    'twine',
    'keyring',
    'artifacts-keyring'
]

setup(
    name='OpenPatchMiner',
    version='0.1.0',
    packages=['opm'],
     python_requires='>=3.6',
    install_requires=requirements,
    url='https://github.com/CBICA/OPM',
    license='BSD-3-Clause License',
    author='Caleb Grenko',
    author_email='software@cbica.upenn.edu',
    description='A patch miner for large histopathology images',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD-3-Clause License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    long_description=readme,
    include_package_data=True,
    keywords='histopathylogy, patch, miner',
    zip_safe=False,
)
