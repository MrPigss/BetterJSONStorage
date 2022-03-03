import setuptools

with open("README.rst", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="BetterJSONStorage",
    version="1.2.4",
    author="Thomas Eeckhout",
    author_email="Thomas.Eeckhout@outlook.be",
    description="An optimized tinyDB storage extension",
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
    install_requires=["tinydb", "orjson", "blosc2", "mypy"],
    python_requires=">=3.6",
    setup_requires=["isort"],
)
