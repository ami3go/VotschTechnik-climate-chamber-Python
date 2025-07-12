import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="VotschTechnikClimateChamber",
    version="0.1.0",  # Follow semantic versioning
    author="Matias H. Senger",
    author_email="m.senger@hotmail.com",
    description="Python interface for Vötsch/Weiss Technik climate chambers with LabEvent controllers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ami3go/VotschTechnik-climate-chamber-Python",
    project_urls={
        "Bug Tracker": "https://github.com/ami3go/VotschTechnik-climate-chamber-Python/issues",
        "Documentation": "https://github.com/ami3go/VotschTechnik-climate-chamber-Python/wiki",
    },
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "votsch-cli=VotschTechnikClimateChamber.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Manufacturing",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
    ],
    keywords="vötsch weiss climate chamber environmental test lab equipment",
    license="MIT",
    include_package_data=True,
    options={
        "bdist_wheel": {
            "universal": True
        }
    },
)