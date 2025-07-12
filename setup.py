import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="VotschTechnikClimateChamber",
    version="0.1.0",
    author="Matias H. Senger",
    author_email="m.senger@hotmail.com",
    description="Python interface for Vötsch/Weiss Technik climate chambers with LabEvent controllers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SengerM/VotschTechnik-climate-chamber-Python",
    project_urls={
        "Bug Tracker": "https://github.com/SengerM/VotschTechnik-climate-chamber-Python/issues",
        "Documentation": "https://github.com/SengerM/VotschTechnik-climate-chamber-Python/wiki",
    },
    packages=setuptools.find_packages(),  # Removed src/ reference
    python_requires=">=3.7",
    install_requires=[
        "pyserial>=3.5",
        "numpy>=1.19.0",
    ],
    extras_require={
        "gui": ["pyqt5>=5.15.0"],
        "test": ["pytest>=6.0", "pytest-cov>=2.0"],
    },
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
    license="MIT",  # Modern license specification
    include_package_data=True,
)