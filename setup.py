# Authors: Russell C., Raife H., Forrest F.
# Date: 2023-11-27
# Copyright: (c) 2023 Aimped
# Description: This is the setup file for the Aimped library.

import setuptools
from aimped.version import __version__

setuptools.setup(
    name="aimped",
    version= __version__,
    packages=setuptools.find_packages(),
    install_requires=[ 
                        'nltk',
                        'pandas',
                        'scikit-learn',
                        "pydantic",
                        "neo4j",
                        "cryptography",
                        "boto3",
                        "jwt",
                        ],
    author="F. Faraday",
    author_email="forest@aimped.ai",
    maintainer="aimped",
    maintainer_email="contact@aimped.ai",
    github="https://github.com/ai-amplified/aimped",
    description="Aimped is a unique library that provides classes and functions for only exclusively business-tailored AI-based NLP models.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://aimped.ai/", 
    
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
