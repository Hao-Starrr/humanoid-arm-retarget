<div style="display:none">
<div align="center">

  <h1 align="center"> Humanoid Arm Retarget </h1>
  <h3 align="center">
    Humanoid arm retargeting to translate human arms motion to 7 degrees of freedom humanoid robot arm motion.
  </h3>
</div>
<p align="center">
  <!-- code check badges -->
  <!-- <a href='https://github.com/Hao-Starrr/humanoid-arm-retarget/blob/main/.github/workflows/test.yml'>
      <img src='https://github.com/Hao-Starrr/humanoid-arm-retarget/actions/workflows/test.yml/badge.svg' alt='Test Status' />
  </a> -->
  <!-- issue badge -->
  <a href="https://github.com/Hao-Starrr/humanoid-arm-retarget/issues">
  <img src="https://img.shields.io/github/issues-closed/Hao-Starrr/humanoid-arm-retarget.svg" alt="Issues Closed">
  </a>
  <a href="https://github.com/Hao-Starrr/humanoid-arm-retarget/issues?q=is%3Aissue+is%3Aclosed">
  <img src="https://img.shields.io/github/issues/Hao-Starrr/humanoid-arm-retarget.svg" alt="Issues">
  </a>
  <!-- release badge -->
  <a href="https://github.com/Hao-Starrr/humanoid-arm-retarget/tags">
  <img src="https://img.shields.io/github/v/release/Hao-Starrr/humanoid-arm-retarget.svg?include_prereleases&sort=semver" alt="Releases">
  </a>
  <!-- pypi badge -->
  <a href="https://github.com/Hao-Starrr/humanoid-arm-retarget/tags">
  <img src="https://static.pepy.tech/badge/dex_retargeting/month" alt="pypi">
  </a>
  <!-- license badge apache -->
  <a href="https://github.com/Hao-Starrr/humanoid-arm-retarget/blob/main/LICENSE">
      <img alt="License" src="https://img.shields.io/badge/License-GNU%20GPL-blue">
  </a>
</p>

## Introduction


## Demo


## Difference with other repo
open Television 
provide ik

unitree
ik different, provide interface to other robot
casadi+pin vs scipy+fk

anyteleop
cobot vs humanoid arm

dex-retargeting
inspire hand


## File Structure

```
-----
|   teleop.py
|         [main function, a loop in 90hz to send commmand to the robot]
|   arms_retarget.py
|         [input human arm frames, optimize and output the 14 joint angles ]
|   hands_retarget.py
|         [input human hand frames, calculate the 6 angles per hand]
|   gesture.py
|         [update the values in main loop, detect the snap]
|   camera_interface.py
|         [capture the images from different cameras]
|   sliverscreen.py
|         [upload the vision streaming to local server]
|   interface.py
|         [controllers, send the commands to robots]
|
|   fftai_gr1.yaml
|   open_loong.yaml
|         [configuration files]
|
+---avp_stream
+---Tracking Streamer
|   Tracking Streamer.xcodeproj
|         [VisionPro app]
```

## Install


## Reference

Park, Y. Teleopeation System using Apple Vision Pro (Version 0.1.0) [Computer software]. https://github.com/Improbable-AI/VisionProTeleop

Rakita, D., Mutlu, B., & Gleicher, M. (2018). RelaxedIK: Real-time Synthesis of Accurate and Feasible Robot Arm Motion. In Proceedings of Robotics: Science and Systems. Pittsburgh, Pennsylvania. 

Cheng, X., Li, J., Yang, S., Yang, G., & Wang, X. (2024). Open-TeleVision: Teleoperation with Immersive Active Visual Feedback. arXiv preprint arXiv:2407.01512.
</div>