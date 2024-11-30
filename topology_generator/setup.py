from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='topology_generator',
    version='0.1.0',
    author='preCICE Research Team',
    author_email='your.email@example.com',
    description='Advanced preCICE Simulation Topology Configuration Generator',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/precice/topology-generator',
    packages=find_packages(),
    install_requires=[
        'pydantic>=2.0.0',
        'pyyaml>=6.0.0',
        'lxml>=4.9.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.3.0',
            'pytest-cov>=4.0.0',
            'mypy>=1.3.0',
            'black>=23.3.0',
            'flake8>=6.0.0',
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.10',
        'Topic :: Scientific/Engineering :: Physics',
    ],
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            'topology-generator=topology_generator.cli:main',
        ],
    },
)
