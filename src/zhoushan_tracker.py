"""
舟山定海渔港专用跟踪器
针对Halo3000雷达和定海海域特点优化
"""

import numpy as np


class ZhoushanKFTracker:
    """定海优化卡尔曼滤波"""

    def __init__(self, dt=1.0, q=0.08, r=0.8):
        self.dt = dt
        self.F = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        self.H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]])
        self.Q = np.eye(4) * q
        self.R = np.eye(2) * r
        self.x = np.zeros((4, 1))
        self.P = np.eye(4)
        self.init = False

    def process(self, x, y):
        if not self.init:
            self.x = np.array([[x], [y], [0], [0]])
            self.init = True
            return x, y
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        z = np.array([[x], [y]])
        y_res = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y_res
        self.P = (np.eye(4) - K @ self.H) @ self.P
        return float(self.x[0, 0]), float(self.x[1, 0])

    def get_state(self):
        return {'x': float(self.x[0, 0]), 'y': float(self.x[1, 0]), 'speed': float(
            np.sqrt(self.x[2, 0]**2 + self.x[3, 0]**2))}


class ZhoushanPFTracker:
    """定海优化粒子滤波"""

    def __init__(self, n=200, q=0.5, r=2.0):
        self.n = n
        self.Q = q
        self.R = r
        self.particles = None
        self.weights = None
        self.state = np.zeros(4)
        self.init = False

    def process(self, x, y):
        if not self.init:
            self.particles = np.zeros((self.n, 4))
            self.particles[:, 0] = np.random.normal(x, 0.5, self.n)
            self.particles[:, 1] = np.random.normal(y, 0.5, self.n)
            self.particles[:, 2] = np.random.normal(0, 0.5, self.n)
            self.particles[:, 3] = np.random.normal(0, 0.5, self.n)
            self.weights = np.ones(self.n) / self.n
            self.state = np.array([x, y, 0, 0])
            self.init = True
            return x, y

        dt = 0.5
        self.particles[:, 0] += self.particles[:, 2] * dt
        self.particles[:, 1] += self.particles[:, 3] * dt
        self.particles[:, 0] += np.random.normal(0, self.Q * 0.1, self.n)
        self.particles[:, 1] += np.random.normal(0, self.Q * 0.1, self.n)

        dx = self.particles[:, 0] - x
        dy = self.particles[:, 1] - y
        like = np.exp(-(dx**2 + dy**2) / (2 * self.R**2 + 1e-6))
        self.weights *= like
        self.weights /= np.sum(self.weights)

        self.state[0] = np.average(self.particles[:, 0], weights=self.weights)
        self.state[1] = np.average(self.particles[:, 1], weights=self.weights)

        if np.random.random() < 0.3:
            idx = np.random.choice(self.n, self.n, p=self.weights)
            self.particles = self.particles[idx]
            self.weights = np.ones(self.n) / self.n

        return float(self.state[0]), float(self.state[1])

    def get_state(self):
        return {'x': float(self.state[0]), 'y': float(self.state[1]), 'speed': float(
            np.sqrt(self.state[2]**2 + self.state[3]**2))}


class ZhoushanFactory:
    @staticmethod
    def create(algo='KF'):
        if algo == 'KF':
            return ZhoushanKFTracker()
        elif algo == 'PF':
            return ZhoushanPFTracker()
        else:
            raise ValueError(f"不支持: {algo}")

    @staticmethod
    def list():
        return ['KF', 'PF']


# 针对Halo3000的参数配置
HALO3000_CONFIG = {
    'radar': {
        'name': 'Simrad Halo3000',
        'frequency': 'X-band (9.39-9.495 GHz)',
        'power': '130W',
        'range': '6m - 96nm',
        'resolution': '0.04 usec',
        'modes': ['Harbour', 'Offshore', 'Weather', 'Bird']
    },
    'zhoushan': {
        'location': '定海渔港',
        'typical_sea_state': '1-3级',
        'main_vessels': ['渔船', '货船', '小型船舶'],
        'traffic_density': '中高'
    },
    'tracking': {
        'algorithm': 'KF',
        'process_noise': 0.08,
        'measurement_noise': 0.8
    }
}


if __name__ == '__main__':
    print("=" * 50)
    print("定海优化算法测试")
    print("=" * 50)

    # 测试KF
    kf = ZhoushanFactory.create('KF')
    err = []
    x = y = 0
    for i in range(50):
        x += 1.5
        y += 0.5
        mx = x + np.random.randn() * 0.3
        my = y + np.random.randn() * 0.3
        ex, ey = kf.process(mx, my)
        err.append(np.sqrt((ex - x)**2 + (ey - y)**2))
    print(f"定海KF误差: {np.mean(err):.4f}")

    # 测试PF
    pf = ZhoushanFactory.create('PF')
    err2 = []
    x = y = 0
    for i in range(50):
        x += 1.5
        y += 0.5
        mx = x + np.random.randn() * 0.3
        my = y + np.random.randn() * 0.3
        ex, ey = pf.process(mx, my)
        err2.append(np.sqrt((ex - x)**2 + (ey - y)**2))
    print(f"定海PF误差: {np.mean(err2):.4f}")
