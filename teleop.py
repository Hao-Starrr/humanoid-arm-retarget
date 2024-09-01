"""
Author: WANG Wenhao
Date: 2024-08-02
Version: 1.0.0
copyright (c) 2024 All Rights Reserved
"""


###################### Hardware Setting ########################
from avp_stream import VisionProStreamer
import numpy as np
import time
from gesture import SnapMonitor
from arms_retarget import ArmRetarget
# from hands_retarget import HandRetarget
import quaternionic
# from interface import UDPServer

s = VisionProStreamer(ip="192.168.0.154")


###################### Initialization ########################
snap_monitor = SnapMonitor()
arm_solver = ArmRetarget()
# hand_solver = HandRetarget()
# server = UDPServer('192.168.0.155', 8010)


###################### Control Initialization ########################
target_control_frequency = 90  # 机器人控制频率
target_control_period_in_s = 1.0 / target_control_frequency  # 机器人控制周期

q_arms = np.array([-np.pi / 12, 0, 0, -np.pi / 6, 0, 0, 0,
                   -np.pi / 12, 0, 0, -np.pi / 6, 0, 0, 0])
q_ready = q_arms
q_lazy = np.zeros(28)

last_valid_q_arms = q_arms
th = target_control_frequency * np.pi/180
# 1 degrees = angle threshold in one iteration
speed_thresholds = np.array([th] * 14)

###################### Mode ########################
Mode = "Detach"


###################### Starting ########################
print("-------------Control Starts--------------")
print("-------------Detach Mode-----------------")


# Main loop:
while True:
    time_start_of_robot_control_loop_in_s = time.time()

    r = s.get_latest()

    snap_monitor.update(r)
    if snap_monitor.left.snap_detected:
        if Mode == "Engage":
            Mode = "Detach"
            # upbody_comm.init_set_pos(q_lazy[6:20])
            print("CHANGE MODE TO DETACH!!!")
        elif Mode == "Detach":
            Mode = "Engage"
            # upbody_comm.init_set_pos(q_ready[6:20])
            print("CHANGE MODE TO ENGAGE!!!")

    if Mode != "Engage":
        # print("---Detach mode---")
        time.sleep(0.01)
        continue

    ### solve arm ###
    t1 = time.time()
    q_arms = arm_solver.solve_arm_angles(q_arms, r)
    t2 = time.time()
    print("solve freqency: ", 1 / (t2 - t1))

    ### check valid ###
    diff = q_arms - last_valid_q_arms
    out_of_bounds = np.any((diff < -speed_thresholds)
                           | (diff > speed_thresholds))
    if out_of_bounds:
        print("### Too far from last valid q_arms!!! Ignored the current command!")
        q_arms = last_valid_q_arms
    else:
        last_valid_q_arms = q_arms

    ### combine and filter ###
    # q_total = np.concatenate((q_upbody, q_arms))

    ### control upbody ###
    # upbody_comm.set_pos(q_total)

    ### solve hand ###
    # left_hand_angles, right_hand_angles = hand_solver.solve_fingers_angles(r)

    ### control hand ###
    # hand_comm.send_hand_cmd(hand_angles[:6], hand_angles[6:])

    ### send control command ###
    # ctrl_cmd = q_arms.tolist().append([0]*14)
    # server.send(ctrl_cmd)

    ### fit control frequency ###
    time_end_of_robot_control_loop_in_s = time.time()
    time_of_robot_control_loop_in_s = (
        time_end_of_robot_control_loop_in_s - time_start_of_robot_control_loop_in_s
    )
    time_to_sleep_in_s = target_control_period_in_s - time_of_robot_control_loop_in_s
    if time_to_sleep_in_s >= 0:
        pass
    else:
        time_to_sleep_in_s = 0
    time.sleep(time_to_sleep_in_s)
