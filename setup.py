import setuptools

import auto_timelapse


# To run: py setup.py sdist bdist_wheel
# To upload: py -m twine upload --sign --skip-existing dist/*
#            py -m twine upload --sign --skip-existing (--comment COMMENT) (--repository testpypi) dist/*


with open('README.md', 'r', encoding='utf-8') as readme_file:
    long_description = readme_file.read()

setuptools.setup(
    name='cmpc-timelapse',
    version=auto_timelapse.__version__,
    author='Joel McBride',
    author_email='joel.mcbride1@live.com',
    license='GPLv3',
    description='Script for automatically downloading a list of videos, speeding them up, and concatenating them.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/JMcB17/auto_timelapse_script',
    py_modules=['auto_timelapse'],
    entry_points={
        'console_scripts': [
            'cmpc-timelapse=auto_timelapse:main'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
    ],
    python_requires='>=3',
    # TODO: figure out bounds for requirements?
    install_requires=[
        'ffmpeg-python',
        'youtube-dl',
    ]
)
