from setuptools import setup
from setuptools import find_packages

package_name = 'scikit-discovery'

package_list = find_packages()

setup(name     = package_name,
      version  = '0.9.9',
      packages = package_list,
      zip_safe = False,
      
      install_requires = ['tqdm',
                          'numpy>=1.10',
                          'pandas>=0.17',
                          'scipy',
                          'setuptools',
                          'astropy>=1.1.2',
                          'scikit-dataaccess>=2.0.0',
                          'psutil>=5',
                          'boto3>=1.4.4',
                          'statsmodels >= 0.8'
                          'graphviz >= 0.7.1',
                          'paramiko> >= 2.1.2',
                          'matplotlib >= 2.0.2',
                          'dispy>=4.8.2',
                          'scikit_image >= 0.13.0',
                          'ipython => 6.1.0',
                          'ipywidgets => 7.0.0b2',
                          'psutil >= 5.2.2',
                          'seaborn >= 0.8',
                          'six >= 1.10.0',
                          'scikit_learn >= 0.19',
                          'traitlets >= 4.3.2',],
      
      description = 'A package for Computer-Aided Discovery',
      author = 'MITHAGI',
      author_email='skdaccess@mit.edu',
      classifiers=[
          'Topic :: Scientific/Engineering',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3 :: Only'
          ],
      python_requires='>=3.4'
)