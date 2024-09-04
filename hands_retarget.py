import numpy as np


def calculate_angle_between_vectors(v1, v2):
    # v1, v2为numpy数组，shape为(3,)
    cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    angle_radians = np.arccos(cos_theta)
    return angle_radians


class HandRetarget:
    def __init__(self):
        # gripper parameters
        # 拇指和食指完全闭合的时候pinch_distance大概是8mm=0.008m
        # 这里设置的阈值是0.02m，即当拇指和食指的距离小于0.02m时，认为想要做pinch动作

        self.pinching_threshold = 0.02
        self.gripper_limits = (0.0, 90.0)

        # fingers parameters
        # 这些数据是需要根据人手大小不同来调的
        # 直接看手部关节数据，自由活动手部，看这些角度的上下限
        # 比如(40.0, 170.0)的意思是握拳的时候四根指头的角度是40，张开是170
        # 会被直接映射到因时机械手输入的0-1000之间
        self.four_fingers_limits = (40.0, 170.0)
        self.thumb_bending_limits = (15.0, 30.0)
        self.thumb_rotation_limits = (80.0, 150.0)

        # cache
        self.last_valid_left = None
        self.last_valid_right = None
        self.last_valid_left_pinch = None
        self.last_valid_right_pinch = None

    def _get_point_angle(self, finger_frames, origin, point1, point2):
        vector1 = finger_frames[point1, :3, 3] - \
            finger_frames[origin, :3, 3]
        vector2 = finger_frames[point2, :3, 3] - \
            finger_frames[origin, :3, 3]
        angle = calculate_angle_between_vectors(
            vector1, vector2)/np.pi*180
        return angle

    def _solve_four_fingers(self, finger_frames):
        # 顺序是 (little, ring, middle, index)
        four_angles = np.zeros(4)
        for i in range(4):
            # 6 to 9, 6 to 5 is index finger
            # plus 5 per finger
            angle = self._get_point_angle(
                finger_frames, 6+5*i, 5+5*i, 9+5*i)
            four_angles[3-i] = angle  # 倒着排

        # 这里两个值应该是人手打开和握拳的角度，映射到0到1000之间
        # 机械手的角度在19到176.7之间
        four_angles = np.clip(four_angles, *self.four_fingers_limits)
        four_angles = (four_angles - self.four_fingers_limits[0]) / (
            self.four_fingers_limits[1] - self.four_fingers_limits[0]) * 1000
        return four_angles

    def _solve_thumb(self, finger_frames, pinch_distance):
        # 在大多数情况下都是直接映射两个自由度
        bending_angle = self._get_point_angle(
            finger_frames, 1, 4, 6)
        rotation_angle = self._get_point_angle(
            finger_frames, 6, 3, 21)

        # bending
        # 人手角度在xx和xx之间，映射到0到1000，
        # 机械手值 -13.0deg 到 53.6deg
        bending_angle = np.clip(bending_angle, *self.thumb_bending_limits)
        bending_angle = (bending_angle - self.thumb_bending_limits[0]) / (
            self.thumb_bending_limits[1] - self.thumb_bending_limits[0]) * 1000

        # rotation
        # 人手角度在xx和xx之间，映射到0到1000，
        # 机械手值 90deg 到 165deg
        rotation_angle = np.clip(rotation_angle, *self.thumb_rotation_limits)
        rotation_angle = (rotation_angle - self.thumb_rotation_limits[0]) / (
            self.thumb_rotation_limits[1] - self.thumb_rotation_limits[0]) * 1000

        # 在pinch模式下例外
        # distance 0.01 到 0.04 之间，线性变换
        # bending_angle 400 到 1000 之间
        # 这里的参数都要根据人手大小来调，即使调的好，解决pinch问题也比较有限，无法捏住很细小的东西
        # 主要原因是六自由度的限制
        is_pinch_mode = pinch_distance < 0.04
        if is_pinch_mode:
            rotation_angle = 150
            pinch_distance = np.clip(pinch_distance, 0.01, 0.04)
            bending_angle = 800 * (pinch_distance - 0.01) / (0.04 - 0.01) + 400

        return bending_angle, rotation_angle

    def solve_fingers_angles(self, r):
        # 如果末端执行器是因时六自由度灵巧手，用这个函数

        # 初始判断需不需要保存cache
        if self.last_valid_left is None:
            self.last_valid_left = r["left_fingers"]
            self.last_valid_left_pinch = r["left_pinch_distance"]
        if self.last_valid_right is None:
            self.last_valid_right = r["right_fingers"]
            self.last_valid_right_pinch = r["right_pinch_distance"]

        # 左手

        # 这里的finger_frames是手指的坐标系，shape为(25, 4, 4)
        # pinch_distance是指尖的距离，标量
        finger_frames = r["left_fingers"]
        pinch_distance = r["left_pinch_distance"]

        # 如果数据是空的，代表visionpro没有检测到手部，给出的数据是无效的
        if finger_frames[1][0, 0] == 0 and finger_frames[1][0, 1] == 0 and finger_frames[1][0, 2] == 0:
            # 使用上一次的有效数据
            finger_frames = self.last_valid_left
            pinch_distance = self.last_valid_left_pinch
        else:
            # 保存当前数据
            self.last_valid_left = finger_frames
            self.last_valid_left_pinch = pinch_distance

        left_four_fingers_angles = self._solve_four_fingers(finger_frames)
        left_thumb_angles = self._solve_thumb(
            finger_frames, pinch_distance)
        left_angles = np.concatenate(
            (left_four_fingers_angles, left_thumb_angles))

        # 右手

        finger_frames = r["right_fingers"]
        pinch_distance = r["right_pinch_distance"]

        if finger_frames[1][0, 0] == 0 and finger_frames[1][0, 1] == 0 and finger_frames[1][0, 2] == 0:
            # 说明是空的
            finger_frames = self.last_valid_right
            pinch_distance = self.last_valid_right_pinch
        else:
            self.last_valid_right = finger_frames
            self.last_valid_right_pinch = pinch_distance

        right_four_fingers_angles = self._solve_four_fingers(finger_frames)
        right_thumb_angles = self._solve_thumb(
            finger_frames, pinch_distance)
        right_angles = np.concatenate(
            (right_four_fingers_angles, right_thumb_angles))

        return left_angles, right_angles
