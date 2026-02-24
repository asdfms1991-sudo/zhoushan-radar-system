"""
惯性跟踪器
用于目标惯性导航和预测
"""

import numpy as np


class InertialTracker:
    """惯性跟踪器 - 基于运动模型的惯性导航"""

    def __init__(self):
        # 状态: [x, y, vx, vy, ax, ay]
        self.state = np.zeros(6)
        self.P = np.eye(6) * 100  # 协方差

        # 状态转移矩阵
        self.F = np.eye(6)
        # 测量矩阵（只测量位置）
        self.H = np.array([[1, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0]])

        self.initialized = False

    def initialize(self, x, y, vx=0, vy=0):
        """初始化"""
        self.state = np.array([x, y, vx, vy, 0, 0])
        self.P = np.eye(6)
        self.initialized = True

    def predict(self, dt=1.0):
        """预测步骤 - 恒定加速度模型"""
        # 更新状态转移矩阵
        self.F[0, 2] = dt
        self.F[0, 4] = dt**2 / 2
        self.F[1, 3] = dt
        self.F[1, 5] = dt**2 / 2
        self.F[2, 4] = dt
        self.F[3, 5] = dt

        # 过程噪声
        q = 0.1
        Q = np.eye(6) * q

        # 预测
        self.state = self.F @ self.state
        self.P = self.F @ self.P @ self.F.T + Q

        return self.state[0], self.state[1]

    def update(self, x, y):
        """更新步骤"""
        if not self.initialized:
            self.initialize(x, y)
            return x, y

        # 测量
        z = np.array([x, y])

        # 卡尔曼增益
        S = self.H @ self.P @ self.H.T + np.eye(2) * 1.0
        K = self.P @ self.H.T @ np.linalg.inv(S)

        # 更新
        y_res = z - self.H @ self.state
        self.state = self.state + K @ y_res
        self.P = (np.eye(6) - K @ self.H) @ self.P

        return self.state[0], self.state[1]

    def process(self, x, y, dt=1.0):
        """一步处理"""
        self.predict(dt)
        return self.update(x, y)

    def get_state(self):
        """获取状态"""
        return {
            'x': float(self.state[0]),
            'y': float(self.state[1]),
            'vx': float(self.state[2]),
            'vy': float(self.state[3]),
            'ax': float(self.state[4]),
            'ay': float(self.state[5]),
            'speed': float(np.sqrt(self.state[2]**2 + self.state[3]**2)),
            'heading': float(np.arctan2(self.state[3], self.state[2]) * 180 / np.pi)
        }

    def predict_ahead(self, seconds=10):
        """预测未来位置"""
        # 预测n秒后的位置
        x = self.state[0] + self.state[2] * \
            seconds + 0.5 * self.state[4] * seconds**2
        y = self.state[1] + self.state[3] * \
            seconds + 0.5 * self.state[5] * seconds**2
        return x, y


class IMMTracker:
    """交互多模型跟踪器 - IMM"""

    def __init__(self):
        # 3个模型：匀速、加速、转弯
        self.models = [
            InertialTracker(),  # 匀速
            InertialTracker(),  # 加速
            InertialTracker(),  # 转弯
        ]

        # 模型概率
        self.model_prob = np.array([0.8, 0.1, 0.1])

        # 切换概率矩阵
        self.transition = np.array([
            [0.9, 0.05, 0.05],
            [0.1, 0.8, 0.1],
            [0.05, 0.15, 0.8]
        ])

        self.initialized = False

    def initialize(self, x, y):
        for model in self.models:
            model.initialize(x, y)
        self.initialized = True

    def predict(self, dt=1.0):
        # 预测所有模型
        for model in self.models:
            model.predict(dt)

    def update(self, x, y):
        if not self.initialized:
            self.initialize(x, y)
            return x, y

        # 更新所有模型
        likelihoods = []
        for model in self.models:
            model.update(x, y)
            # 计算似然（简化）
            dx = model.state[0] - x
            dy = model.state[1] - y
            like = np.exp(-(dx**2 + dy**2) / 10)
            likelihoods.append(like)

        likelihoods = np.array(likelihoods)

        # 更新模型概率
        self.model_prob *= likelihoods
        self.model_prob /= self.model_prob.sum()

        # 混合状态估计
        x_est = sum(
            m.state[0] * p for m,
            p in zip(
                self.models,
                self.model_prob))
        y_est = sum(
            m.state[1] * p for m,
            p in zip(
                self.models,
                self.model_prob))

        return x_est, y_est

    def process(self, x, y, dt=1.0):
        self.predict(dt)
        return self.update(x, y)

    def get_state(self):
        return {
            'x': sum(m.state[0] * p for m, p in zip(self.models, self.model_prob)),
            'y': sum(m.state[1] * p for m, p in zip(self.models, self.model_prob)),
            'vx': sum(m.state[2] * p for m, p in zip(self.models, self.model_prob)),
            'vy': sum(m.state[3] * p for m, p in zip(self.models, self.model_prob)),
            'model_probs': self.model_prob.tolist()
        }


class GatedTracker:
    """门控跟踪器 - 用于目标关联"""

    def __init__(self, gate_threshold=3.0):
        self.gate_threshold = gate_threshold

    def gate(self, measurements, predicted):
        """门控 - 筛选候选测量"""
        gated = []
        for z in measurements:
            dist = np.sqrt((z[0] - predicted[0])**2 + (z[1] - predicted[1])**2)
            if dist < self.gate_threshold:
                gated.append(z)
        return gated


# 测试
if __name__ == '__main__':
    print("=" * 50)
    print("惯性跟踪测试")
    print("=" * 50)

    # 测试惯性跟踪
    it = InertialTracker()
    errors = []
    x = y = 0
    for i in range(50):
        x += 1.5
        y += 0.5
        mx = x + np.random.randn() * 0.3
        my = y + np.random.randn() * 0.3
        ex, ey = it.process(mx, my)
        errors.append(np.sqrt((ex - x)**2 + (ey - y)**2))

    print(f"惯性跟踪误差: {np.mean(errors):.4f}")

    # 测试IMM
    print("\nIMM测试:")
    imm = IMMTracker()
    errors2 = []
    x = y = 0
    for i in range(50):
        x += 1.5
        y += 0.5
        mx = x + np.random.randn() * 0.3
        my = y + np.random.randn() * 0.3
        ex, ey = imm.process(mx, my)
        errors2.append(np.sqrt((ex - x)**2 + (ey - y)**2))

    print(f"IMM误差: {np.mean(errors2):.4f}")
