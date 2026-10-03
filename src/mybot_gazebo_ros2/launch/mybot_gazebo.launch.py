"""
Gazebo Sim(Fortress) + mybot 스폰 + ros_gz_bridge + robot_state_publisher

실행:  ros2 launch mybot_gazebo_ros2 mybot_gazebo.launch.py
       (GUI 없이) ros2 launch mybot_gazebo_ros2 mybot_gazebo.launch.py headless:=true

월드는 gazebo.launch.py 의 world = ... 줄에서 바꾼다 (교재 8.4.1 방식).
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument,
                            IncludeLaunchDescription)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    pkg_gazebo = get_package_share_directory('mybot_gazebo_ros2')
    pkg_desc = get_package_share_directory('mybot_description')

    # URDF 의 package:// 메시 경로를 Gazebo 가 찾을 수 있도록 share 디렉터리 등록
    set_resource_path = AppendEnvironmentVariable(
        'IGN_GAZEBO_RESOURCE_PATH', os.path.dirname(pkg_desc))

    robot_description = xacro.process_file(
        os.path.join(pkg_desc, 'urdf', 'mybot.xacro')).toxml()

    # 1) Gazebo + 월드 (월드 파일은 gazebo.launch.py 에서 지정)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo, 'launch', 'gazebo.launch.py')),
    )

    # 2) robot_state_publisher (joint_state_publisher 는 사용하지 않음: Gazebo 가 /joint_states 발행)
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description,
                     'use_sim_time': True}],
    )

    # 3) 로봇 스폰 (구: gazebo_ros spawn_entity.py)
    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description',
                   '-name', 'mybot',
                   '-x', '0.0', '-y', '0.0', '-z', '0.15'],
        output='screen',
    )

    # 4) 브릿지.  [ : Gazebo -> ROS,  ] : ROS -> Gazebo
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V',
            '/joint_states@sensor_msgs/msg/JointState[ignition.msgs.Model',
            '/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
            '/imu@sensor_msgs/msg/Imu[ignition.msgs.IMU',
        ],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('headless', default_value='false',
                              description='true 면 Gazebo GUI 없이 서버만 실행'),
        set_resource_path,
        gazebo,
        rsp,
        spawn,
        bridge,
    ])
