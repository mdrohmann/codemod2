try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

description = (
    "Codemod2 is a tool/library to assist you with large-scale codebase "
    "refactors that can be partially automated but still require human "
    "oversight and occasional intervention. Codemod2 was originally developed "
    "at Facebook and released as open source.  It now uses the pcre2 engine "
    "for patter matching."
)

setup(
    name="codemod2",
    version="1.0.0",
    url="http://github.com/mdrohmann/codemod2",
    license="Apache License 2.0",
    author="Martin Drohmann",
    author_email="mdrohmann@gmail.com",
    description=description,
    long_description=description,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms="any",
    entry_points="""
        [console_scripts]
        codemod2=codemod2.base:main
    """,
    tests_require=["flake8", "pytest"],
    test_suite="py.test",
)
