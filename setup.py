from setuptools import setup, find_packages


requires = {
    'setup': [
    ],
    'install': [
        'gevent'
    ],
    'tests': [
        'pytest',
        'pytest-cov',
        'pytest-flake8',
        'requests',
    ],
}

requires['all'] = list({dep for deps in requires.values() for dep in deps})


def readme():
    with open('README.md', 'r') as f:
        return f.read()

setup(
    name='gevent-breaker',
    version='1.0.0',
    description='Circuitbreaker pattern for gevent apps',
    long_description=readme(),
    url='http://github.com/daroot/gevent-breaker',
    author='Dan Root',
    author_email='rootdan+pypi@gmail.com',
    license='WTFPL',

    packages=find_packages(),
    setup_requires=requires['setup'],
    install_requires=requires['install'],
    tests_require=requires['tests'],
    extras_require=requires,
    include_package_data=True,
    zip_safe=False,
    platforms='any',

    keywords=['pytest', 'consul'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: Freely Distributable',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
