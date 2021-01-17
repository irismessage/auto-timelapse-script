import setuptools


# To run: python setup.py sdist bdist_wheel
# To upload: python -m twine upload (--repository testpypi) dist/*


with open("README.md", "r", encoding="utf-8") as readme_file:
    long_description = readme_file.read()

# TODO: test distribution and put on real pypi
setuptools.setup(
    name="cmpc-timelapse",
    version="0.6.4",
    author="Joel McBride",
    author_email="joel.mcbride1@live.com",
    description="Script for automatically downloading a list of videos, speeding them up, and concatenating them.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JMcB17/auto_timelapse_script",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
    ],
    python_requires='>=3',
    # TODO: figure out bounds for requirements?
    install_requires=[
        'ffmpeg-python',
        'youtube-dl',
    ]
)
