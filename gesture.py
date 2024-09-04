
import numpy as np
import time


class SnapMonitorOneSide:
    def __init__(self, chirality=None):
        self.hand_side = chirality

        self.snap_detected = False
        self.last_snap_time = 0
        self.prev_distance13 = None
        self.prev_distance03 = None
        self.prev_movement1 = None
        self.last_update_time = 0

        # set threshold
        self.cooldown = 1.1
        self.threshold_speed13 = 0.20
        self.threshold_speed03 = 0.20
        self.threshold_speed1 = 0.30

    def update(self, fingers):
        current_time = time.time()
        time_interval = current_time - self.last_update_time
        if time_interval < 0.1:
            self.snap_detected = False
            return

        self.last_update_time = current_time

        thumbTipPos = fingers[4, :3, 3]
        indexTipPos = fingers[9, :3, 3]
        middleTipPos = fingers[14, :3, 3]
        distance13 = np.linalg.norm(thumbTipPos - middleTipPos)
        distance03 = np.linalg.norm(middleTipPos)
        if self.hand_side == 'left':
            movement1 = thumbTipPos[0] - thumbTipPos[1] - thumbTipPos[2]
        if self.hand_side == 'right':
            movement1 = -thumbTipPos[0] + thumbTipPos[1] + thumbTipPos[2]

        # initialize previous values
        if self.prev_distance13 is None:
            self.prev_distance13 = distance13
            self.prev_distance03 = distance03
            self.prev_movement1 = movement1
            return

        # calculate the speed
        speed13 = (distance13 - self.prev_distance13)/time_interval
        speed03 = (self.prev_distance03 - distance03)/time_interval
        speed1 = (movement1 - self.prev_movement1)/time_interval
        distance23 = np.linalg.norm(indexTipPos - middleTipPos)

        # main function
        if (speed13 > self.threshold_speed13 and
            speed03 > self.threshold_speed03 and
                speed1 > self.threshold_speed1):
            if current_time - self.last_snap_time > self.cooldown:
                self.snap_detected = True
                self.last_snap_time = current_time
        else:
            self.snap_detected = False

        # update previous value
        self.prev_distance13 = distance13
        self.prev_distance03 = distance03
        self.prev_movement1 = movement1


# call: snap_monitor = SnapMonitor()
# flag: snap_monitor.left.snap_detected or snap_monitor.right.snap_detected
class SnapMonitor:
    def __init__(self):
        self.left = SnapMonitorOneSide(chirality='left')
        self.right = SnapMonitorOneSide(chirality='right')

    def update(self, r):
        self.left.update(r['left_fingers'])
        self.right.update(r['right_fingers'])
