from setuptools import setup, find_packages

setup(
    name="geo-toolkit-indonesia",
    version="1.0.0",
    description="A Python geoscience toolkit for coordinate conversion, survey calculations, well-log reading, GIS export, and visualization — built for Indonesia O&G workflows.",
    author="GeoToolkit Indonesia",
    python_requires=">=3.8",
    packages=find_packages(),
    package_data={
        "geo_toolkit_indonesia": ["data/sample/*"],
    },
    install_requires=[
        "pyproj>=3.4.0",
        "lasio>=0.31",
        "numpy>=1.21",
        "matplotlib>=3.5",
        "scipy>=1.9",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "pytest-cov"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
)
