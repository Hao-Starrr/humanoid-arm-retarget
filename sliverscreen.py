import asyncio
import time
from enum import Enum

import cv2
import numpy as np
from vuer import Vuer
from vuer.schemas import Hands, ImageBackground

from camera_interface import CameraType, RealsenseAsyncContext, ZedAsyncContext


class MovingAverage:
    def __init__(self, window_size):
        self.window_size = window_size
        self.window = []

    def next(self, val):
        if len(self.window) < self.window_size:
            self.window.append(val)
            return sum(self.window) / len(self.window)
        else:
            self.window.pop(0)
            self.window.append(val)
            return sum(self.window) / self.window_size

    def get(self):
        return sum(self.window) / len(self.window)


class Silverscreen:
    def __init__(self, camera_type: CameraType, fps=60, use_cert=False):
        try:
            if camera_type == CameraType.ZED:
                self.camera_context = ZedAsyncContext
            elif camera_type == CameraType.REALSENSE:
                self.camera_context = RealsenseAsyncContext

        except:
            print(f"Camera type {camera_type} not supported")
            exit()
        if use_cert:
            self.app = Vuer(
                host="0.0.0.0",
                cert="./cert.pem",
                key="./key.pem",
                queries=dict(grid=False),
            )
        else:
            self.app = Vuer(host="0.0.0.0", queries=dict(grid=False))
        self.app.add_handler("HAND_MOVE", self.on_hand_move)
        self.app.add_handler("CAMERA_MOVE", self.on_cam_move)
        self.app.spawn(self.main, start=False)

        self.fps = fps

        self.left_hand = np.zeros((4, 4))
        self.right_hand = np.zeros((4, 4))
        self.left_landmarks = np.zeros((25, 3))
        self.right_landmarks = np.zeros((25, 3))
        self.head_matrix = np.zeros((4, 4))
        self.all_data = None
        self.aspect = 1.0

    async def on_cam_move(self, event, session):
        self.head_matrix = np.asarray(event.value["camera"]["matrix"]).reshape(
            (4, 4), order="F"
        )
        self.aspect = event.value["camera"]["aspect"]

    async def on_hand_move(self, event, session):
        self.left_hand = np.asarray(
            event.value["leftHand"]).reshape((4, 4), order="F")
        self.right_hand = np.asarray(event.value["rightHand"]).reshape(
            (4, 4), order="F"
        )
        self.left_landmarks = np.asarray(
            event.value["leftLandmarks"]).reshape((25, 3))
        self.right_landmarks = np.asarray(event.value["rightLandmarks"]).reshape(
            (25, 3)
        )
        self.all_data = event.value

    async def main(self, session):
        session.upsert @ Hands(fps=self.fps, stream=True, key="hands")
        measured_duration = MovingAverage(10)
        async with self.camera_context({"camera_resolution": (720, 1280)}) as ctx:
            while True:
                start = time.time()
                if ctx.type == CameraType.ZED:
                    left_image, right_image = await ctx.grab()
                    session.upsert(
                        [
                            ImageBackground(
                                left_image,
                                format="jpeg",
                                quality=40,
                                key="left-image",
                                interpolate=True,
                                aspect=1.778,
                                distanceToCamera=2,
                                layers=1,
                            ),
                            ImageBackground(
                                right_image,
                                format="jpeg",
                                quality=40,
                                key="right-image",
                                interpolate=True,
                                aspect=1.778,
                                distanceToCamera=2,
                                layers=2,
                            ),
                        ],
                        to="bgChildren",
                    )
                elif ctx.type == CameraType.REALSENSE:
                    color_image, depth_image = await ctx.grab()
                    session.upsert(
                        [
                            ImageBackground(
                                color_image,
                                format="jpeg",
                                quality=40,
                                key="left-image",  # todo: figure out what this means
                                interpolate=True,
                                aspect=1.778,
                                distanceToCamera=2,
                                position=[0, -0.5, -2],
                                rotation=[0, 0, 0],
                            ),

                        ],
                        to="bgChildren",
                    )
                duration = time.time() - start
                measured_duration.next(duration)
                text = f"time (ms): {measured_duration.get() * 1000.0: >#8.3f}"
                print(text, end="\r")
                await asyncio.sleep(1 / self.fps)


if __name__ == "__main__":
    ss = Silverscreen(CameraType.REALSENSE, use_cert=True)
    ss.app.run()
