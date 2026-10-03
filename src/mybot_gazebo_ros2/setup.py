import os
from glob import glob
from setuptools import setup

package_name = 'mybot_gazebo_ros2'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.sdf')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pmice',
    maintainer_email='pmice@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # Gazebo Classic .world -> Gazebo Sim .sdf 변환 (교재 8.3 Building Editor 월드용)
            'convert_world = mybot_gazebo_ros2.convert_world:main',
        ],
    },
)
