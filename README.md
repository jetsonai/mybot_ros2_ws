# mybot_ros2_ws

ros2 foxy mybot

## teleop

ros2 launch mybot_gazebo_ros2 mybot_gazebo.launch.py

ros2 launch mybot_gazebo_ros2 mybot_gazebo_rviz.launch.py

ros2 run mybot_teleop teleop_keyboard

-----------------

# slam

ros2 launch mybot_gazebo_ros2 mybot_gazebo.launch.py

ros2 launch mybot_cartographer cartographer.launch.py use_sim_time:=True

ros2 run mybot_teleop teleop_keyboard

ros2 run nav2_map_server map_saver_cli -f ~/map2


-------------------

# navi2

ros2 launch mybot_gazebo_ros2 mybot_gazebo.launch.py

ros2 launch mybot_navigation2 navigation2.launch.py map:=$HOME/map.yaml use_sim_time:=True

-------------------------------------

apt install ros-foxy-joint-state-publisher ros-foxy-joint-state-publisher-gui ros-foxy-xacro ros-foxy-gazebo-ros ros-foxy-gazebo-ros-pkgs


---------------------------








