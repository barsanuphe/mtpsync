"""MTPSync.
Select FLAC files, convert to mp3, and sync with MTP device.
"""

# Always prefer setuptools over distutils
from setuptools import setup

setup(
    name='mtpsync',
    version='1.0.0',
    description='Select FLAC files, convert to mp3, and sync with MTP device.',
    # long_description=long_description,
    url='https://github.com/barsanuphe/XXXXX',
    author='barsanuphe',
    author_email='mon.adresse.publique@gmail.com',
    license='GPLv3+',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 2 - Pre-Alpha'
        'Intended Audience :: End Users/Desktop',
        'Operating System :: POSIX :: Linux',
        'Topic :: Multimedia :: Sound/Audio :: Conversion',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='mtp flac mp3 convert sync',
    packages=['mtpsync'],

    install_requires=['pyyaml', 'notify2', 'progressbar', 'rgain'],  # , 'xdg'],

    entry_points={
        'console_scripts': [
            'mtpsync=mtpsync:main',
        ],
    },

)
