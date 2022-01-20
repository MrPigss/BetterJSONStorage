import setuptools

with open("README.rst", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="BetterJSONStorage",
    version="0.4.4",
    author="Thomas Eeckhout",
    author_email="Thomas.Eeckhout@outook.be",
    description="A tinyDB storage extension using a faster json compiler and compression",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/MrPigss/BetterJSONStorage",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Database",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    install_requires=['tinydb', 'orjson','blosc'],
    python_requires=">=3.5",
)