#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    sllidar_dir = get_package_share_directory('sllidar_ros2')
    slam_dir = get_package_share_directory('slam_toolbox')

    # launch the lidar
    lidar = IncludeLaunchDescription( 
        PythonLaunchDescriptionSource(
            os.path.join(sllidar_dir, 'launch', 'sllidar_a1_launch.py')),
        launch_arguments={'serial_port': '/dev/ttyUSB0'}.items(),
    )

    # base_link -> laser. TUNE x y z to where the lidar is mounted on the kart.
    laser_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'laser'],
    )

    # launch the odom
    odom = Node(
        package='move_motor',
        executable='odom_node',
        name='odom_node',
        output='screen',
    )

    # launch the SLAM
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_dir, 'launch', 'online_async_launch.py')),
        launch_arguments={'use_sim_time': 'false'}.items(),
    )

    return LaunchDescription([lidar, laser_tf, odom, slam])
