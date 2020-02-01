from setuptools import setup, find_packages

setup(
    name="local-dns-tools",
    packages=find_packages(),
    install_requires=[
        'falcon',
        'gunicorn',
        'ruamel.yaml',
        'gitpython',
    ],
)
