"""
Gazebo Sim(Fortress) + mybot 스폰 + ros_gz_bridge + robot_state_publisher

실행:  ros2 launch mybot_gazebo_ros2 mybot_gazebo.launch.py                 (기본: myworld.sdf)
       ros2 launch mybot_gazebo_ros2 mybot_gazebo.launch.py world:=example.sdf
       (GUI 없이) ros2 launch mybot_gazebo_ros2 mybot_gazebo.launch.py headless:=true
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument,
                            IncludeLaunchDescription)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    headless = LaunchConfiguration('headless')

    pkg_gazebo = get_package_share_directory('mybot_gazebo_ros2')
    pkg_desc = get_package_share_directory('mybot_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # worlds/ 폴더 안의 파일 이름을 world 인자로 선택
    world = PathJoinSubstitution([pkg_gazebo, 'worlds', LaunchConfiguration('world')])

    # URDF 의 package:// 메시 경로를 Gazebo 가 찾을 수 있도록 share 디렉터리 등록
    set_resource_path = AppendEnvironmentVariable(
        'IGN_GAZEBO_RESOURCE_PATH', os.path.dirname(pkg_desc))

    robot_description = xacro.process_file(
        os.path.join(pkg_desc, 'urdf', 'mybot.xacro')).toxml()

    # 1) Gazebo 서버(+GUI). -r : 시작하자마자 시뮬레이션 재생
    gz_sim_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': ['-r ', world]}.items(),
        condition=UnlessCondition(headless),
    )
    gz_sim_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': ['-r -s ', world]}.items(),
        condition=IfCondition(headless),
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
        DeclareLaunchArgument('world', default_value='myworld.sdf',
                              description='worlds/ 폴더의 월드 파일 (myworld.sdf, example.sdf)'),
        DeclareLaunchArgument('headless', default_value='false',
                              description='true 면 Gazebo GUI 없이 서버만 실행'),
        set_resource_path,
        gz_sim_gui,
        gz_sim_headless,
        rsp,
        spawn,
        bridge,
    ])
