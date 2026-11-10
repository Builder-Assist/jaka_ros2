# Fork pitfalls and known gaps

This fork of [JAKARobotics/jaka_ros2](https://github.com/JAKARobotics/jaka_ros2) (upstream commit f6b28c6)
is adapted to controllers running **Coboπ 3.x** (tested: Coboπ 3.3.12 on a Zu 30, ROS 2 Jazzy).
Changes are kept minimal so that upstream can still be merged. This file lists what was
deliberately **not** changed and the traps that follow from it.

## What this fork changes

- SDK library and headers updated in `jaka_driver` and `jaka_planner` (the two copies must stay identical).
- `jaka_driver` and `moveit_server` log in over gRPC with the account given by the environment
  variables `JAKA_SDK_USERNAME` and `JAKA_SDK_PASSWORD`; `moveit_server` exits when the login fails.
- `libjakaAPI.so` is installed by CMake (no manual copy into the install tree).
- `jaka_planner/launch/moveit_real_robot.launch.py`: MoveIt 2 with the real robot without the
  `launches.py` patch of the MoveIt installation.
- `jaka_zu30_moveit_config`: joint acceleration limits enabled (placeholder value, see below).

## Controller prerequisites (not enforced by the code)

- Coboπ 3.x no longer serves the legacy SDK TCP ports 10001/10004. The SDK needs the HTTPS login
  service on port 20006 and the TLS gRPC endpoint on port 50053.
- An SDK user account must exist on the controller. Unset credentials give controller error
  917507 (incorrect username), a wrong password gives 917506 and **counts toward the password
  lockout**. Verify the credentials in the controller web UI before retrying from ROS.
- The control source must be set to *Remote* in the app, otherwise `power_on` and every motion
  command fail with SDK code 10007 (gRPC PERMISSION_DENIED, "please switch to Remote control
  source by APP").
- `jaka_driver` and `moveit_server` cannot run at the same time (upstream limitation).

## Not implemented

1. **`sdk_test.cpp`** still uses the legacy two-argument `login_in` (TCP mode) and cannot connect
   to a Coboπ 3.x controller. Left as upstream.
2. **Error messages.** The driver's error map only knows the classic SDK codes. gRPC errors are
   reported by the SDK as `10000 + grpc status code` and produce an empty
   `"error occurred:"` service response. The real reason is in the SDK log,
   `/tmp/jaka_sdk_logs/<robot_ip>/jakaLog.txt`.
3. **Acceleration limits.** JAKA publishes no joint acceleration figure (checked in the
   "JAKA 2025 Product Selection Guide"). `jaka_zu30_moveit_config` uses a conservative
   1.0 rad/s² placeholder; the 21 other `jaka_*_moveit_config` packages still have
   `has_acceleration_limits: false`, so planning with the default Jazzy pipeline fails for them.
4. **`moveit_server` safety.** No robot state is published, the result of `servo_j` is logged but
   not acted upon, and goal cancellation is commented out. A trajectory executes immediately once
   accepted. Keep first motions small and the e-stop in reach.
5. **Tool and user frames.** There is no service to read or switch the active tool
   (`get_tool_id`, `set_tool_id`) or user frame (`set_user_frame_id`). `set_toolframe` and
   `set_userframe` only *define* a slot (with the fixed names "ToolCoord" / "BaseCoord") and never
   activate it. The active user frame id is only visible in the `frame_id` of
   `/jaka_driver/tool_position`.
6. **Simulation launch.** `jaka_<model>_moveit_config/launch/demo.launch.py` still needs the
   patched `launches.py` from the documentation (section 4.2) for the RViz simulation mode, and
   fails against a real robot (it starts `ros2_control` without a hardware plugin). Use
   `moveit_real_robot.launch.py` for the real robot.
7. **Credentials handling.** The environment variables are read once at login. `ros2 launch`
   inherits the shell environment; a sourced setup script does not set them.
