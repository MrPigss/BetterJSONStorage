import setuptools

setuptools.setup(
    name="BetterJSONStorage",
    version="1.3.2",
    author="Thomas Eeckhout",
    author_email="Thomas.Eeckhout@outlook.be",
    description="An optimized tinyDB storage extension",
    url="https://github.com/MrPigss/BetterJSONStorage",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Database",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    install_requires=["tinydb", "orjson", "blosc2", "mypy"],
    python_requires=">=3.8",
    setup_requires=["isort"],
)
