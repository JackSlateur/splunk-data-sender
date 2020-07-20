from setuptools import setup, find_packages

setup(
    name='splunk_data_sender',
    version='0.0.1',
    license='MIT License',
    description='A Python logging handler that sends your logs to Splunk',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Andrea Salvatori',
    author_email='andrea.salvatori92@gmail.com',
    url='https://github.com/Sonic0/splunk-data-sender',
    packages=find_packages(),
    install_requires=['requests >= 2.24.0, < 3.0.0'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: System :: Logging'
    ]
)