"""
简化版粒子滤波器
稳定版本
"""

import numpy as np


class SimplePFTracker:
    """简化稳定的粒子滤波"""
    
    def __init__(self, num_particles=200):
        self.n = num_particles
        self.particles = None
        self.weights = None
        self.state = np.zeros(2)
        self.init = False
        self.r = 1.0  # 测量噪声
        self.q = 0.5  # 过程噪声
    
    def process(self, x, y):
        if not self.init:
            # 初始化
            self.particles = np.zeros((self.n, 2))
            self.particles[:, 0] = np.random.normal(x, 0.5, self.n)
            self.particles[:, 1] = np.random.normal(y, 0.5, self.n)
            self.weights = np.ones(self.n) / self.n
            self.state = np.array([x, y])
            self.init = True
            return x, y
        
        # 预测 - 加噪声
        self.particles[:, 0] += np.random.normal(0, self.q, self.n)
        self.particles[:, 1] += np.random.normal(0, self.q, self.n)
        
        # 计算权重
        dx = self.particles[:, 0] - x
        dy = self.particles[:, 1] - y
        dist = dx**2 + dy**2
        
        # 高斯权重
        weights = np.exp(-dist / (2 * self.r**2))
        weights /= (weights.sum() + 1e-10)
        
        # 状态估计
        self.state[0] = np.sum(weights * self.particles[:, 0])
        self.state[1] = np.sum(weights * self.particles[:, 1])
        
        # 简化重采样 - 加权随机采样
        if np.random.random() < 0.5:
            try:
                weights_norm = weights / (weights.sum() + 1e-10)
                idx = np.random.choice(self.n, self.n, p=weights_norm)
                self.particles = self.particles[idx]
            except:
                pass  # 采样失败就跳过
        
        return self.state[0], self.state[1]
    
    def get_state(self):
        return {'x': float(self.state[0]), 'y': float(self.state[1])}


def create(algorithm='KF'):
    """工厂"""
    if algorithm == 'PF':
        return SimplePFTracker()
    else:
        from advanced_tracker import KFTracker
        return KFTracker()


if __name__ == '__main__':
    print("简化PF测试:")
    pf = SimplePFTracker()
    err = []
    x = y = 0
    for i in range(50):
        x += 1.5
        y += 0.5
        mx = x + np.random.randn()*0.3
        my = y + np.random.randn()*0.3
        ex, ey = pf.process(mx, my)
        err.append(np.sqrt((ex-x)**2+(ey-y)**2))
    print(f"简化PF误差: {np.mean(err):.4f}")
