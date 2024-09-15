
import importlib
import yaml
import numpy as np
import scipy.optimize as opt
import quaternionic


def calculate_angle_between_vectors(v1, v2):

    cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    angle_radians = np.arccos(cos_theta)
    return angle_radians


class ArmRetarget:
    def __init__(self, config_file="open_loong.yaml"):
        # 加载配置文件
        self.config = self.load_config(config_file)

        # 加载左右臂的FK函数
        self.left_fk = self.load_fk_function('left_fk_function')
        self.right_fk = self.load_fk_function('right_fk_function')

        # 缩放比例
        self.scale_factor = self.config['scale_factor']

        # 获取关节数量
        self.num_joints = self.config['num_joints']

        # 将角度限制转换为弧度
        self.lower_bounds = np.array(self.config['lower_bounds']) * np.pi / 180
        self.upper_bounds = np.array(self.config['upper_bounds']) * np.pi / 180

        # 创建优化边界
        self.bounds = [(l, u)
                       for l, u in zip(self.lower_bounds, self.upper_bounds)]

        self.last_optimized_q_10d = np.array(
            self.config['init_q']) * np.pi / 180

        # 加载左右臂的基础变换矩阵
        self.left_base = np.array(self.config['left_base'])
        self.right_base = np.array(self.config['right_base'])
        self.left_wrist = np.array(self.config['left_wrist'])
        self.right_wrist = np.array(self.config['right_wrist'])

        # 缓存上一次有效的结果
        self.last_valid_r = None

    def load_config(self, config_file):
        """加载YAML配置文件"""
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)

    def load_fk_function(self, fk_key):
        """动态加载FK函数"""
        module_name, function_name = self.config[fk_key].rsplit('.', 1)
        module = importlib.import_module(module_name)
        return getattr(module, function_name)

    def _fi(self, n, s, c, r, x):
        return (-1) ** n * np.exp(-((x - s) ** 2) / (2 * c**2)) + r * (x - s) ** 4

    def _position_cost(self, target_pos, actual_pos):
        n, s, c, r = 1, 0, 0.2, 5.0
        xl = np.linalg.norm(target_pos[0] - actual_pos[0])
        xr = np.linalg.norm(target_pos[1] - actual_pos[1])

        return self._fi(n, s, c, r, xl) + self._fi(n, s, c, r, xr)

    def _orientation_cost(self, target_quat, actual_quat):
        n, s, c, r = 1, 0, 0.2, 5.0
        q1 = quaternionic.array(target_quat[0])
        q2 = quaternionic.array(actual_quat[0])
        xl = quaternionic.distance.rotation.intrinsic(q1, q2)
        q1 = quaternionic.array(target_quat[1])
        q2 = quaternionic.array(actual_quat[1])
        xr = quaternionic.distance.rotation.intrinsic(q1, q2)

        return self._fi(n, s, c, r, xl) + self._fi(n, s, c, r, xr)

    def _joint_velocity_cost(self, q0_10d, q_10d):
        n, s, c, r = 1, 0, 0.2, 5.0
        xll = q0_10d[0:5] - q_10d[0:5]
        xll[0:3] = xll[0:3] * 2
        xl = np.linalg.norm(xll)
        xrr = q0_10d[5:10] - q_10d[5:10]
        xrr[0:3] = xrr[0:3] * 2
        xr = np.linalg.norm(xrr)
        return self._fi(n, s, c, r, xl) + self._fi(n, s, c, r, xr)

    def _singularity_cost(self, q_10d):
        pass

    def _objective_function(self, q_10d):
        """优化目标函数"""
        # 将10维关节角度扩展为14维
        q0_14d = np.zeros(14)
        q0_14d[0:5] = q_10d[0:5]
        q0_14d[7:12] = q_10d[5:10]

        # 计算左右臂的FK
        r_left = self.left_fk(q0_14d[0:7])
        r_right = self.right_fk(q0_14d[7:14])
        # print("q_10d     : ", q_10d)
        # print("r_left    : ", r_left)
        # print("r_right   : ", r_right)

        # 获取机械臂当前实际位置和方向
        actual_pos = np.vstack((r_left[0], r_right[0]))
        actual_quat = np.vstack((r_left[1], r_right[1]))

        # 用机械臂当前状态和目标状态 计算位置、方向和速度的代价
        pos_cost = self._position_cost(self.target_pos, actual_pos)
        ori_cost = self._orientation_cost(self.target_quat, actual_quat)
        vel_cost = self._joint_velocity_cost(self.last_optimized_q_10d, q_10d)

        # 返回加权总代价
        return 60 * pos_cost + 6 * ori_cost + 2 * vel_cost

    def _solve_wrist_angles(self, T_wrist, T_forearmWrist, chirality=None):
        # self.T_wrist, self.T_forearmWrist 算最后两个关节的角度

        # 按照GR1T2的系约定
        # wrist y 和 arm y 的夹角 是招手自由度的角度，朝着arm x的方向为向内招手
        wrist_y = T_wrist[:3, 1]
        arm_y = T_forearmWrist[:3, 1]
        angle6 = calculate_angle_between_vectors(wrist_y, arm_y)
        arm_x = T_forearmWrist[:3, 0]
        if np.dot(arm_x, wrist_y) > 0:
            # 向内招手 右手+
            if chirality == "left":
                q6 = -angle6
            elif chirality == "right":
                q6 = angle6
        else:
            # 向外招手 左手+
            if chirality == "left":
                q6 = angle6
            elif chirality == "right":
                q6 = -angle6

        # wrist z 和 -arm z 的夹角 是摆手自由度的角度，朝着arm x的方向为向外摆手
        wrist_z = T_wrist[:3, 2]
        arm_z = T_forearmWrist[:3, 2]
        angle7 = calculate_angle_between_vectors(wrist_z, -arm_z)
        arm_x = T_forearmWrist[:3, 0]
        if np.dot(arm_x, wrist_z) > 0:
            # 向外摆手 左手右手+
            if chirality == "left":
                q7 = angle7
            elif chirality == "right":
                q7 = angle7
        else:
            # 向内
            if chirality == "left":
                q7 = -angle7
            elif chirality == "right":
                q7 = -angle7

        # 限制关节角度
        q7 = np.clip(q7, -np.pi * 35 / 180, np.pi * 35 / 180)
        q6 = np.clip(q6, -np.pi * 50 / 180, np.pi * 55 / 180)

        return q7, q6  # reverse 6 and 7 because rcs interface error

    def _solve_uparm_angles(self, q0, target_pos, target_quat):
        self.target_pos = target_pos
        self.target_quat = target_quat

        # 应该输入10维，然后在objecive function里补成14维
        q0_10d = np.concatenate((q0[0:5], q0[7:12]))
        result = opt.minimize(
            self._objective_function,
            q0_10d,
            method="SLSQP",
            tol=1e-3,
            bounds=self.bounds,
            options={"maxiter": 100},
        )

        if result.success:
            optimized_q = result.x
            # print("optimized_q: ", optimized_q)
            # print("Optimization successful! Joint angles: ", optimized_q)

            self.last_optimized_q_10d = optimized_q
            return optimized_q
        else:
            raise Exception(
                "Optimization failed! After "
                + result.nit
                + " iterations."
                + result.message
            )

    def solve_arm_angles(self, q0, r):
        """求解手臂角度"""
        # 处理缺失数据
        if self.last_valid_r is None:
            self.last_valid_r = r

        is_left_missing = np.all(r["left_fingers"][1][0, :3] == 0)
        is_right_missing = np.all(r["right_fingers"][1][0, :3] == 0)
        if is_left_missing or is_right_missing:
            r = self.last_valid_r
        else:
            self.last_valid_r = r

        # 获取手腕和前臂的变换矩阵
        left_wrist = r["left_wrist"][0]
        right_wrist = r["right_wrist"][0]
        left_forearmWrist = left_wrist @ r["left_fingers"][-2]
        right_forearmWrist = right_wrist @ r["right_fingers"][-2]

        q_2d_l = self._solve_wrist_angles(
            left_wrist, left_forearmWrist, chirality="left")
        q_2d_r = self._solve_wrist_angles(
            right_wrist, right_forearmWrist, chirality="right")

        # 机器人的fk有不同的起点
        # 人的坐标起点是VR world frame
        # 因此要把人的手腕和前臂的起点转换到机器人的左右手base坐标系
        # 这是第一个矩阵乘法@的作用

        # 因为系的定义不同，人和机器人在同样姿态下ee的系也不同
        # 需要对其两者的ee，才能比较误差
        # 这是第二个矩阵乘法@的作用
        left_forearmWrist = self.left_base @ left_forearmWrist @ self.left_wrist
        right_forearmWrist = self.right_base @ right_forearmWrist @ self.right_wrist
        pos = np.vstack((left_forearmWrist[:3, 3], right_forearmWrist[:3, 3]))
        pos = pos * self.scale_factor
        quat1 = quaternionic.array.from_rotation_matrix(left_forearmWrist)
        quat2 = quaternionic.array.from_rotation_matrix(right_forearmWrist)
        quat = np.vstack((quat1, quat2))

        # 求解上臂角度
        q_10d = self._solve_uparm_angles(q0, pos, quat)

        # 组合所有关节角度
        q_14d = np.concatenate((q_10d[0:5], q_2d_l, q_10d[5:10], q_2d_r))

        return q_14d
