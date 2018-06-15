from setuptools import setup, find_packages

setup(
    name="visualization_shopify_tools",
    version="0.1.0",
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    package_dir={
        'funnel_tree_vis': 'funnel_tree_vis',
        'plotify': 'plotify'
    }
)
