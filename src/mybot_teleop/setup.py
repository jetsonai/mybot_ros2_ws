from setuptools import find_packages
from setuptools import setup
import os
from glob import glob

package_name = 'mybot_teleop'

setup(
    name=package_name,
    version='2.1.4',
    packages=find_packages(exclude=[]),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))) 
    ],
    install_requires=[
        'setuptools',
    ],
    zip_safe=True,
    author='Kate Kim',
    author_email='jetsonai@jetsonai.com',
    keywords=['ROS'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
    description=(
        'Teleoperation node using keyboard for RSaemBot.'
    ),
    license='Apache License, Version 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'teleop_keyboard = mybot_teleop.teleop_keyboard:main'
        ],
    },
)
