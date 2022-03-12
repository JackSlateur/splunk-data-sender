from setuptools import setup, find_packages

setup(
    name='splunk_data_sender',
    version='0.3.0',
    license='MIT License',
    description='A Python connector that sends your data to Splunk',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Andrea Salvatori',
    author_email='andrea.salvatori92@gmail.com',
    url='https://github.com/Sonic0/splunk-data-sender',
    packages=find_packages(),
    install_requires=['requests >= 2.27.0, < 3.0.0'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: System :: Logging'
    ],
    python_requires='>=3.6',
)
