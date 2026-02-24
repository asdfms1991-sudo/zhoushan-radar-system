"""
Kalman滤波模块
用于目标跟踪的状态估计
"""

import numpy as np
from typing import Optional, Tuple


class KalmanFilter:
    """
    Kalman Filter 实现

    用于目标跟踪的状态估计，包含预测和更新两个步骤
    """

    def __init__(self, dt: float = 1.0, process_noise: float = 0.1, measurement_noise: float = 1.0):
        """
        初始化 Kalman Filter

        Args:
            dt: 时间步长（秒）
            process_noise: 过程噪声Q
            measurement_noise: 测量噪声R
        """
        self.dt = dt
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise

        # 状态向量：[x, y, vx, vy]
        self.state = np.zeros((4, 1))
        # 状态协方差矩阵
        self.P = np.eye(4) * 100
        # 状态转移矩阵
        self.F = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        # 测量矩阵（只测量位置）
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])
        # 过程噪声协方差矩阵
        self.Q = np.eye(4) * process_noise
        # 测量噪声协方差矩阵
        self.R = np.eye(2) * measurement_noise

        self.initialized = False

    def initialize(self, x: float, y: float):
        """初始化状态"""
        self.state[0, 0] = x
        self.state[1, 0] = y
        self.state[2, 0] = 0  # vx
        self.state[3, 0] = 0  # vy
        self.P = np.eye(4) * 1
        self.initialized = True

    def predict(self) -> Tuple[float, float]:
        """
        预测步骤

        Returns:
            预测的位置 (x, y)
        """
        # 状态预测
        self.state = self.F @ self.state
        # 协方差预测
        self.P = self.F @ self.P @ self.F.T + self.Q

        return self.state[0, 0], self.state[1, 0]

    def update(self, x: float, y: float) -> Tuple[float, float]:
        """
        更新步骤

        Args:
            x, y: 测量位置

        Returns:
            更新后的位置 (x, y)
        """
        if not self.initialized:
            self.initialize(x, y)
            return x, y

        # 测量向量
        z = np.array([[x], [y]])

        # 预测测量
        z_pred = self.H @ self.state

        # 残差
        y = z - z_pred

        # 残差协方差
        S = self.H @ self.P @ self.H.T + self.R

        # Kalman增益
        K = self.P @ self.H.T @ np.linalg.inv(S)

        # 状态更新
        self.state = self.state + K @ y
        self.P = (np.eye(4) - K @ self.H) @ self.P

        return self.state[0, 0], self.state[1, 0]

    def predict_update(self, x: float, y: float) -> Tuple[float, float]:
        """
        预测+更新（单步）

        Args:
            x, y: 测量位置

        Returns:
            估计位置 (x, y)
        """
        self.predict()
        return self.update(x, y)

    def get_velocity(self) -> Tuple[float, float]:
        """获取速度"""
        return self.state[2, 0], self.state[3, 0]

    def get_state(self) -> dict:
        """获取完整状态"""
        return {
            'x': float(self.state[0, 0]),
            'y': float(self.state[1, 0]),
            'vx': float(self.state[2, 0]),
            'vy': float(self.state[3, 0]),
            'speed': float(np.sqrt(self.state[2, 0]**2 + self.state[3, 0]**2)),
            'P': self.P.tolist()
        }


class MultiTargetKalmanFilter:
    """多目标 Kalman 滤波器"""

    def __init__(self):
        self.filters = {}

    def add_target(self, target_id: str, x: float, y: float,
                   process_noise: float = 0.1, measurement_noise: float = 1.0):
        """添加目标"""
        kf = KalmanFilter(
            process_noise=process_noise,
            measurement_noise=measurement_noise
        )
        kf.initialize(x, y)
        self.filters[target_id] = kf

    def update_target(self, target_id: str, x: float, y: float) -> Optional[dict]:
        """更新目标状态"""
        if target_id not in self.filters:
            self.add_target(target_id, x, y)
            return self.filters[target_id].get_state()

        kf = self.filters[target_id]
        kf.predict_update(x, y)
        return kf.get_state()

    def predict_target(self, target_id: str) -> Optional[tuple]:
        """预测目标位置"""
        if target_id not in self.filters:
            return None
        return self.filters[target_id].predict()

    def remove_target(self, target_id: str):
        """移除目标"""
        if target_id in self.filters:
            del self.filters[target_id]

    def get_all_states(self) -> dict:
        """获取所有目标状态"""
        return {
            tid: kf.get_state()
            for tid, kf in self.filters.items()
        }


if __name__ == '__main__':
    # 测试
    import math

    # 创建滤波器
    kf = KalmanFilter(dt=1.0, process_noise=0.1, measurement_noise=1.0)

    # 模拟目标运动（直线）
    true_x, true_y = 0, 0
    vx, vy = 2, 1  # 速度

    positions = []
    estimates = []

    for i in range(10):
        # 真实位置
        true_x += vx
        true_y += vy

        # 添加测量噪声
        measure_x = true_x + np.random.randn() * 0.5
        measure_y = true_y + np.random.randn() * 0.5

        # Kalman预测+更新
        est_x, est_y = kf.predict_update(measure_x, measure_y)

        positions.append((measure_x, measure_y))
        estimates.append((est_x, est_y))

        print(f"Step {i+1}: True=({true_x:.2f},{true_y:.2f}) "
              f"Measure=({measure_x:.2f},{measure_y:.2f}) "
              f"Estimate=({est_x:.2f},{est_y:.2f})")

    # 计算误差
    errors = [math.sqrt((p[0]-e[0])**2 + (p[1]-e[1])**2)
              for p, e in zip(positions, estimates)]
    print(f"\n平均误差: {sum(errors)/len(errors):.3f}")
