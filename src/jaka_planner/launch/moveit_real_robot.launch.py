"""MoveIt 2 with a real JAKA robot, in one launch file.

Starts the jaka_planner moveit_server (SDK connection, FollowJointTrajectory
action server, /joint_states), move_group and RViz for the selected model.

Unlike `jaka_<model>_moveit_config/launch/demo.launch.py`, this does not start
ros2_control: trajectories are executed on the robot by moveit_server. It only
uses the stock `moveit_configs_utils` helpers, so no modification of the MoveIt
installation (the patched `launches.py`) is required.

    ros2 launch jaka_planner moveit_real_robot.launch.py model:=zu30 ip:=10.5.5.100

Arguments:
    ip            IP address of the robot controller.
    model         JAKA model name (zu3, zu30, s5, ...), selects jaka_<model>_moveit_config.
    use_rviz      Start RViz with the MoveIt motion planning plugin (default: true).
    start_server  Start moveit_server here (default: true). Set to false when
                  moveit_server.launch.py is already running in another terminal.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import (
    generate_move_group_launch,
    generate_rsp_launch,
    generate_static_virtual_joint_tfs_launch,
)


def _launch_setup(context, *args, **kwargs):
    # The model name is needed as a plain string to locate the MoveIt config package.
    model = LaunchConfiguration("model").perform(context)
    moveit_config = MoveItConfigsBuilder(
        f"jaka_{model}", package_name=f"jaka_{model}_moveit_config"
    ).to_moveit_configs()

    actions = [
        Node(
            package="jaka_planner",
            executable="moveit_server",
            name="moveit_server",
            output="screen",
            parameters=[{"ip": LaunchConfiguration("ip"), "model": model}],
            condition=IfCondition(LaunchConfiguration("start_server")),
        ),
        generate_rsp_launch(moveit_config),
        generate_static_virtual_joint_tfs_launch(moveit_config),
        generate_move_group_launch(moveit_config),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                str(moveit_config.package_path / "launch/moveit_rviz.launch.py")
            ),
            condition=IfCondition(LaunchConfiguration("use_rviz")),
        ),
    ]
    return actions


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("ip", default_value="10.5.5.100", description="Robot controller IP address"),
            DeclareLaunchArgument("model", default_value="zu3", description="JAKA model (zu3, zu30, s5, ...)"),
            DeclareLaunchArgument("use_rviz", default_value="true", description="Start RViz"),
            DeclareLaunchArgument(
                "start_server",
                default_value="true",
                description="Start moveit_server (false if moveit_server.launch.py already runs)",
            ),
            OpaqueFunction(function=_launch_setup),
        ]
    )
