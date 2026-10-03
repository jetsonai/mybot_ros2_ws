import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    headless = LaunchConfiguration('headless', default='false')

    # 사용할 월드: worlds 폴더 안의 파일 이름으로 바꾼다 (example.sdf / myworld.sdf)
    mybot_gazebo = get_package_share_directory('mybot_gazebo_ros2')
    world = os.path.join(mybot_gazebo, "worlds", "example.sdf")

    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    return LaunchDescription([
        # Gazebo 창 + 시뮬레이션 (-r : 켜자마자 재생)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments={'gz_args': '-r ' + world}.items(),
            condition=UnlessCondition(headless),
        ),

        # headless:=true 이면 Gazebo 창 없이 시뮬레이션만 (-s)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments={'gz_args': '-r -s ' + world}.items(),
            condition=IfCondition(headless),
        ),
    ])
