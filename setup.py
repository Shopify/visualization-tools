from setuptools import setup, find_packages

setup(
    name="funnel-tree-visualization",
    version="0.1.0",
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    package_dir={'funnel-tree-visualization': 'funnel-tree-visualization'}
)
