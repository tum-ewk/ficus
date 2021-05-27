from setuptools import setup, find_packages

with open('requirements/base.pip') as f:
    BASE_REQS = f.read().splitlines()

setup(
    name='ficus',
    version='1.0.0',
    use_scm_version=True,
    packages=find_packages(where='ficus'),
    package_dir={'': 'ficus'},
    package_data={'': ['*.json']},
    install_requires=BASE_REQS,
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3.7'
    ]
)
