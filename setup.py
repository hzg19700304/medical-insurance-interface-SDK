"""医保接口SDK安装配置"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="medical-insurance-sdk",
    version="1.0.0",
    author="Medical Insurance SDK Team",
    author_email="dev@medical-insurance-sdk.com",
    description="通用医保接口SDK，支持多医院部署",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/medical-insurance-sdk/medical-insurance-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
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
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
        "web": [
            "fastapi>=0.85.0",
            "uvicorn>=0.18.0",
        ],
        "async": [
            "aiohttp>=3.8.0",
            "asyncio-mqtt>=0.11.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "medical-insurance-sdk=medical_insurance_sdk.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "medical_insurance_sdk": ["config/*.yaml", "sql/*.sql"],
    },
)