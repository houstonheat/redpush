from setuptools import setup

setup(
    name='redpush',
    version='0.3',
    py_modules=['cli'],
    include_package_data=True,
    packages=['redpush'],
    install_requires=[
        'click==6.7',
        'requests==2.18.4',
        'ruamel.yaml==0.16.5',
        'python-slugify==4.0.0'
    ],
    entry_points='''
        [console_scripts]
        redpush=redpush.cli:cli
    ''',
)
