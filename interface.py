import socket
import json


class UDPServer:
    def __init__(self, server_ip, server_port):
        # 设置UDP服务器地址和端口
        self.server = (server_ip, server_port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.1)

    def send(self, control_cmd):
        self.socket.sendto(
            bytes(json.dumps(control_cmd), "utf-8"), self.server)

    def send_raw(self, control_cmd: bytes):
        self.socket.sendto(
            control_cmd, self.server)
        # print('sent: ', control_cmd, 'to: ', self.server)


class ArmController:
    def __init__(self):
        # 初始化机械臂控制器
        pass

    def send_cmd(self, q_arms):
        # 发送控制命令到机械臂
        print(f"发送机械臂控制命令: {q_arms}")


class HandController:
    def __init__(self):
        # 初始化手部控制器
        pass

    def send_cmd(self, left_hand_angles, right_hand_angles):
        # 发送控制命令到左右手
        print(f"发送左手控制命令: {left_hand_angles}")
        print(f"发送右手控制命令: {right_hand_angles}")

# 如果需要其他辅助函数或类，可以在这里添加
