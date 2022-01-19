from setuptools import setup, find_packages

setup(
    name='BetterJSONStorage',
    version='0.4',
    license='MIT',
    author="Thomas Eeckout",
    author_email='thomas.eeckout@outlook.be',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    keywords='tinydb orjson blosc compressed database storage-extension',
    install_requires=[
          'orjson',
          'blosc'
      ],
)