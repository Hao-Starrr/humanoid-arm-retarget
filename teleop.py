###################### Hardware Setting ########################
import numpy as np
import quaternionic
import time
from avp_stream import VisionProStreamer
from gesture import SnapMonitor
from arms_retarget import ArmRetarget
from hands_retarget import HandRetarget
from interface import ArmController
from interface import HandController
from loop_rate_limiters import RateLimiter


###################### Initialization ########################
s = VisionProStreamer(ip="192.168.0.154")
snap_monitor = SnapMonitor()
arm_solver = ArmRetarget()
hand_solver = HandRetarget()
arm_control = ArmController()
hand_control = HandController()


###################### Control Initialization ########################
freq = 90.0  # 机器人控制频率
rate = RateLimiter(frequency=freq)

q_arms = np.array([-np.pi / 12, 0, 0, -np.pi / 6, 0, 0, 0,
                   -np.pi / 12, 0, 0, -np.pi / 6, 0, 0, 0])
q_ready = q_arms
q_lazy = np.zeros(14)

last_valid_q_arms = q_arms
th = freq * np.pi/180
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
            arm_control.send_cmd(q_lazy)
            print("CHANGE MODE TO DETACH!!!")
        elif Mode == "Detach":
            Mode = "Engage"
            arm_control.send_cmd(q_ready)
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

    ### filter ###
    # filtered_q_arms

    ### solve hand ###
    left_hand_angles, right_hand_angles = hand_solver.solve_fingers_angles(r)

    ### control arm ###
    arm_control.send_cmd(q_arms)

    ### control hand ###
    hand_control.send_cmd(left_hand_angles, right_hand_angles)

    ### fit control frequency ###
    rate.sleep()
