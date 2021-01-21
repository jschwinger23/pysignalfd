from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='pysignalfd',
    py_modules=['pysignalfd'],
    version='0.0.1',
    license='BSD',
    description='A pure Python wrapper of signalfd(2)',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='lzc',
    author_email='greyschwinger@gmail.com',
    url='https://github.com/jschwinger23/pysignalfd',
    platform=('linux'),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Utilities',
    ],
    python_requires='>=3.5',
)
