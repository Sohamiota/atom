from setuptools import find_packages, setup


def get_long_description():
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except:
        return "Atom - System Health Monitor by Times Internet Limited"

def get_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except:
        return ["psutil>=5.8.0"]

setup(
    name="atom-monitor",
    version="1.0.0",
    author="Soham Biswas",
    author_email="soham.biswas@timesinternet.in",
    maintainer="Times Internet Limited",
    description="Atom - A comprehensive system health monitoring tool by Times Internet",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/TimesInternet/atom-monitor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.7",
    install_requires=get_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "atom=atom.monitor:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    license="Proprietary",
)
