from setuptools import setup, find_packages

setup(
    name="arbitrage-bot",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.28.0",
        "python-dotenv>=0.19.0",
        "pytz>=2021.3",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
        ],
    },
    python_requires=">=3.8",
) 