import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="iotawattpy",
    version="0.0.7",
    author="Greg Diehl",
    author_email="greg.diehl.gtd@gmail.com",
    description="Python library for the IoTaWatt Energy device",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gtdiehl/iotawattpy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "httpx>=0.16.1"
    ],
    python_requires='>=3.8',
)
