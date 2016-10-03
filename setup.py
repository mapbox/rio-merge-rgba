from codecs import open as codecs_open
from setuptools import setup, find_packages

# Get the long description from the relevant file
long_description = """
A `rio merge` alternative optimized for large RGBA scenetifs

`rio merge-rgba` is a CLI with nearly identical arguments to `rio merge`. They accomplish the same task, merging many rasters into one. The differences are in the implementation:

`rio merge-rgba`::

1. only accepts 4-band RGBA rasters
2. writes the destination data to disk rather than an in-memory array
3. reads/writes in windows corresponding to the destination block layout
4. once a window is filled with data values, the rest of the source files are skipped for that window

This is both faster and more memory efficient but limited to RGBA rasters.
"""

setup(name='rio-merge-rgba',
      version='0.2.0',
      description=u"rio merge alternative optimized for RGBA",
      long_description=long_description,
      classifiers=[],
      keywords='',
      author=u"Matthew Perry",
      author_email='perry@mapbox.com',
      url='https://github.com/mapbox/rio-merge-rgba',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'click',
          'rasterio'
      ],
      extras_require={
          'test': ['pytest', 'pytest-cov'],
      },
      entry_points="""
      [rasterio.rio_plugins]
      merge-rgba=merge_rgba.scripts.cli:merge_rgba
      """
      )
