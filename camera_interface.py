from enum import Enum

import cv2
import numpy as np

try:
    import pyrealsense2 as rs
except:
    print("RealSense SDK not installed")

try:
    import pyzed.sl as sl
except:
    print("ZED SDK not installed")


class CameraType(Enum):
    ZED = 1
    REALSENSE = 2


class CameraAsyncContext:
    def __init__(self, type: CameraType, init_params=None):
        self.init_params = init_params
        self.type = type
        self.client = None

    # 在 async with 语句开始时调用，通常用于初始化资源。
    async def __aenter__(self):
        pass

    # 在 async with 语句结束时调用，通常用于清理资源。
    async def __aexit__(self, exc_type, exc, tb):
        pass

    # 异步方法 grab 可以在执行过程中暂停，等待I/O操作完成，然后再继续执行。
    async def grab(self):
        pass


class ZedAsyncContext(CameraAsyncContext):
    def __init__(self, init_params=None):
        super().__init__(
            CameraType.ZED,
            {
                "camera_resolution": sl.RESOLUTION.HD720,
                "camera_fps": 30,
                "depth_mode": sl.DEPTH_MODE.PERFORMANCE,
                "coordinate_units": sl.UNIT.METER,
                "depth_minimum_distance": 0.2,  # in meters
                "depth_maximum_distance": 20.0,  # in meters
            },
        )
        if init_params is not None:
            self.init_params.update(init_params)

    async def __aenter__(self):
        if self.client is None:
            self.client = sl.Camera()
            init_params = sl.InitParameters()
            init_params.camera_resolution = self.init_params["camera_resolution"]
            init_params.camera_fps = self.init_params["camera_fps"]
            init_params.depth_mode = self.init_params["depth_mode"]
            init_params.coordinate_units = self.init_params["coordinate_units"]
            init_params.depth_minimum_distance = self.init_params[
                "depth_minimum_distance"
            ]
            init_params.depth_maximum_distance = self.init_params[
                "depth_maximum_distance"
            ]

            err = self.client.open(init_params)
            if err != sl.ERROR_CODE.SUCCESS:
                raise RuntimeError(f"Failed to open ZED camera: {repr(err)}")

        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.client.close()
        self.client = None

    async def grab(self):
        left_image = sl.Mat()
        right_image = sl.Mat()

        if self.client.grab() == sl.ERROR_CODE.SUCCESS:
            self.client.retrieve_image(left_image, sl.VIEW.LEFT)
            self.client.retrieve_image(right_image, sl.VIEW.RIGHT)

            return self.convert_to_ndarray(left_image), self.convert_to_ndarray(
                right_image
            )

    def convert_to_ndarray(self, image):
        image_array = cv2.cvtColor(image.numpy(), cv2.COLOR_BGRA2RGB)
        return image_array


class RealsenseAsyncContext(CameraAsyncContext):

    def __init__(self, init_params=None):
        super().__init__(
            CameraType.REALSENSE,
            {"camera_resolution": (720, 1280),
             "camera_fps": 30, "enable_depth": False},
        )
        if init_params is not None:
            self.init_params.update(init_params)
        self.enable_depth = self.init_params["enable_depth"]
        self.align = None

    async def __aenter__(self):
        if self.client is None:
            for d in rs.context().devices:
                device_name = d.get_info(rs.camera_info.name)
                print(f"Connected to device: {device_name}")
            self.client = rs.pipeline()
            config = rs.config()
            config.enable_stream(
                rs.stream.color,
                self.init_params["camera_resolution"][1],
                self.init_params["camera_resolution"][0],
                rs.format.rgb8,
                self.init_params["camera_fps"],
            )
            if self.enable_depth:
                config.enable_stream(
                    rs.stream.depth,
                    self.init_params["camera_resolution"][1],
                    self.init_params["camera_resolution"][0],
                    rs.format.z16,
                    self.init_params["camera_fps"],
                )
            self.client.start(config)
            if self.enable_depth:
                self.align = rs.align(rs.stream.color)

            sensor = self.client.get_active_profile(
            ).get_device().query_sensors()[1]
            sensor.set_option(rs.option.enable_auto_exposure, True)
            sensor.set_option(rs.option.enable_auto_white_balance, False)
            # sensor.set_option(rs.option.exposure, 156.000)

        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.client.stop()
        self.client = None

    async def grab(self):
        frames = self.client.wait_for_frames()

        if self.enable_depth:
            aligned_frames = self.align.process(frames)

            # Get aligned frames
            aligned_color_frame = aligned_frames.get_color_frame()
            aligned_depth_frame = aligned_frames.get_depth_frame()

            color_image = np.asanyarray(aligned_color_frame.get_data())
            depth_image = np.asanyarray(aligned_depth_frame.get_data())
            return color_image, depth_image
        else:
            depth_image = None

        color_frame = frames.get_color_frame()
        color_image = np.asanyarray(color_frame.get_data())
        # color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
        return color_image, depth_image
