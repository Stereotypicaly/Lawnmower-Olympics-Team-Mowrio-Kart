#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch_ros.actions import Node, LifecycleNode
from launch.actions import TimerAction, ExecuteProcess
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # movement_dir = get_package_share_directory('follow_the_gap')

    # gap_params = os.path.join(movement_dir, 'config', 'gap_params.yaml')
    # use the slam map 
    wheel_node = Node(
        package='move_motor',
        executable='move_gpio_node',
        name='move_gpio_node',
        output='screen',
        emulate_tty=True,
        # parameters=[gap_params],
    )

    wheel_node = Node(
        package='move_motor',
        executable='move_wheel_node',
        name='move_wheel_node',
        output='screen',
        emulate_tty=True,
        # parameters=[gap_params],
    )

    return LaunchDescription([
        gpio_node, wheel_node
    ])