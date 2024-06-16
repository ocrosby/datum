from setuptools import setup, find_packages

setup(
    name='SoccerData',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        # add your project dependencies here
        # for example:
        # 'numpy',
        # 'pandas',
    ],
    entry_points={
        'console_scripts': [
            # if you want to make a script callable from the command line, add an entry here
            # for example:
            # 'soccerdata = soccerdata.main:main',
        ],
    },
)