import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="inferenceql",  # Replace with your own username
    version="0.0.1",
    license='Apache License, Version 2.0',
    packages=[
        'inferenceql',
        'inferenceql.auto_modeling',
    ],
    package_dir={
        'inferenceql': 'src/inferenceql',
        'inferenceql.auto_modeling': 'src/inferenceql/auto_modeling',
    },
    author="Ulrich Schaechtle",  # Maintainer
    author_email="ulli@mit.edu",
    description="Automated data modeling for inferenceQL",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Apache License Version 2.0, January 2004",
        "Operating System :: macOS, Ubuntu",
    ],
    python_requires='>=3.6',
)
