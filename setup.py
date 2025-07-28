# -*- coding: utf-8 -*-
# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open("README.md") as f:
    readme = f.read()

with open("LICENSE.txt") as f:
    license = f.read()

extras_require = {
    "gui": [
        "dash-bootstrap-components>=2.0.3",
        "plotly>=6.2.0",
        "dash>=3.1.1",
    ],
    "deep-learning": [
        "tokenizers>=0.21.2",
        "datasets>=4.0.0",
        "torch>=2.7.1",
        "transformers>=4.53.3",
    ],
    "dev": [
        
    ]
}
extras_require["all"] = sum(extras_require.values(), [])

setup(
    name="rdk_one3b",
    version="0.0.1",
    description="AI-Powered Fault Detection, Prediction and Auto-Healing for Home connectivity",
    long_description_content_type="text/markdown",
    long_description=readme,
    author="Arumugam Panchatcharam, Sivasubramanian, Vasanthakumar, Vandana, Divya Kamatagi, Siddharth Nair, Aditya",
    author_email="telekom-digital.com",
    python_requires=">=3.9.6",
    install_requires=[
        "scikit-learn>=1.6.1",
        "pandas>=2.3.1",
        "numpy>=2.0.2",
        "PyYAML>=6.0.2",
        "attrs>=25.3.0",

        "schema>=0.7.5",
        "salesforce-merlion>=1.0.0",
        "Cython>=0.29.30",
        "nltk>=3.6.5",
        "gensim>=4.1.2",
        "spacy>=3.2.2",
        "dataclasses>=0.6",
        "tqdm>=4.62.3",
        "cachetools>=4.2.4",
        "matplotlib>=3.5.1",
        "seaborn>=0.11.2",
        "Jinja2>=3.0.0",
        "numba>=0.56.3",
    ],
    extras_require=extras_require,
    license=license,
    packages=find_packages(exclude=["tests", "tests.*", "docs", "gui", "gui.*"]),    
    include_package_data=True,
)
