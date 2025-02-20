from setuptools import setup

APP = ['UI.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'includes': ['tkinter', 'scipy'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
