"""Setup configuration for Agent Collaboration Platform."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="agent-collaboration-platform",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A distributed multi-agent system demonstrating asynchronous agent-to-agent communication",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/agent-collaboration-platform",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "black==23.12.0",
            "pylint==3.0.0",
            "pytest==7.4.3",
            "pytest-cov==4.1.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/agent-collaboration-platform/issues",
        "Documentation": "https://github.com/yourusername/agent-collaboration-platform/docs",
        "Source Code": "https://github.com/yourusername/agent-collaboration-platform",
    },
)
