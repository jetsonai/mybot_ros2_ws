# mybot_ros2_ws

ros2 foxy mybot


apt install ros-foxy-joint-state-publisher ros-foxy-joint-state-publisher-gui ros-foxy-xacro ros-foxy-gazebo-ros ros-foxy-gazebo-ros-pkgs


---------------------------

mkdir -p ~/build

cd build

git clone https://github.com/brektrou/rtl8821CU.git

cd rtl8821CU/

lsusb

make

sudo apt install build-essential

sudo apt update

cd rtl8821CU/

sudo apt install dkms

sudo ./dkms-install.sh

sudo modprobe 8821cu





