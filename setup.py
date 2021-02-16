import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="scythe",
    version="0.4",
    license="MIT",
    author="Sean Collings",
    author_email="sean@seanrcollings.com",
    description="Harvests are always better with a good tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    zip_safe=False,
    python_requires=">=3.9",
    entry_points={"console_scripts": ["scythe = scythe.cli:cli"]},
    install_requires=["arc-cli>=2.0.1", "requests", "pyyaml"],
)
