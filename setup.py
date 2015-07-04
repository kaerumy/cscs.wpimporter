from setuptools import setup, find_packages
import os

version = '1.0'

setup(name='cscs.wpimporter',
      version=version,
      description="Wordpress Importer",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='',
      author_email='',
      url='http://svn.plone.org/svn/collective/',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['cscs'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'BeautifulSoup',
          'python-dateutil'
          # -*- Extra requirements: -*-
      ],
      entry_points={
        'console_scripts': [
            'wpxml_to_json = cscs.wpimporter.extractor:main'
        ]
      }
      )
