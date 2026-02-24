"""
优化版粒子滤波器
针对舟山定海渔港特点优化
"""

import numpy as np


class OptimizedPFTracker:
    """优化版粒子滤波"""
    
    def __init__(self, num_particles=300, process_noise=0.3, measurement_noise=1.5):
        self.num_particles = num_particles
        self.Q = process_noise
        self.R = measurement_noise
        
        self.particles = None
        self.weights = None
        self.state = np.zeros(4)
        self.initialized = False
        
        # 速度限制
        self.max_speed = 35  # 渔船最大35节
        
    def initialize(self, x, y):
        """初始化粒子"""
        self.particles = np.zeros((self.num_particles, 4))
        
        # 在测量点周围高斯分布
        self.particles[:, 0] = np.random.normal(x, 0.3, self.num_particles)
        self.particles[:, 1] = np.random.normal(y, 0.3, self.num_particles)
        
        # 初始速度为0附近
        self.particles[:, 2] = np.random.normal(0, 0.3, self.num_particles)
        self.particles[:, 3] = np.random.normal(0, 0.3, self.num_particles)
        
        # 初始化权重
        self.weights = np.ones(self.num_particles) / self.num_particles
        
        self.state = np.array([x, y, 0, 0])
        self.initialized = True
        
        return x, y
    
    def predict(self, dt=1.0):
        """预测步骤"""
        # 恒定速度模型 + 噪声
        self.particles[:, 0] += self.particles[:, 2] * dt + np.random.normal(0, self.Q, self.num_particles)
        self.particles[:, 1] += self.particles[:, 3] * dt + np.random.normal(0, self.Q, self.num_particles)
        
        # 限制位置范围（避免发散）
        self.particles[:, 0] = np.clip(self.particles[:, 0], 29.5, 30.5)
        self.particles[:, 1] = np.clip(self.particles[:, 1], 121.5, 122.5)
        
    def update(self, x, y):
        """更新步骤"""
        # 计算权重（似然）
        dx = self.particles[:, 0] - x
        dy = self.particles[:, 1] - y
        
        # 使用混合高斯噪声模型
        innovation = dx**2 + dy**2
        likelihood = np.exp(-innovation / (2 * self.R**2 + 1e-6))
        
        # 防止权重退化
        self.weights *= likelihood + 1e-10
        
        # 归一化
        weight_sum = np.sum(self.weights)
        if weight_sum > 0:
            self.weights /= weight_sum
        else:
            self.weights = np.ones(self.num_particles) / self.num_particles
        
        # 状态估计（加权平均）
        self.state[0] = np.sum(self.weights * self.particles[:, 0])
        self.state[1] = np.sum(self.weights * self.particles[:, 1])
        self.state[2] = np.sum(self.weights * self.particles[:, 2])
        self.state[3] = np.sum(self.weights * self.particles[:, 3])
        
    def resample(self):
        """重采样 - 系统重采样"""
        # 计算有效粒子数
        neff = 1.0 / np.sum(self.weights**2)
        
        # 阈值判断
        if neff < self.num_particles / 3:
            # 系统重采样
            indices = self._systematic_resample()
            self.particles = self.particles[indices]
            self.weights = np.ones(self.num_particles) / self.num_particles
    
    def _systematic_resample(self):
        """系统重采样"""
        cumsum = np.cumsum(self.weights)
        
        # 生成采样点
        u0 = np.random.uniform(0, 1.0 / self.num_particles)
        u = u0 + np.arange(self.num_particles) / self.num_particles
        
        # 采样
        indices = np.zeros(self.num_particles, dtype=int)
        j = 0
        for i in range(self.num_particles):
            while cumsum[j] < u[i]:
                j += 1
            indices[i] = j
            
        return indices
    
    def process(self, x, y):
        """处理一步"""
        if not self.initialized:
            return self.initialize(x, y)
        
        self.predict()
        self.update(x, y)
        self.resample()
        
        return self.state[0], self.state[1]
    
    def get_state(self):
        """获取状态"""
        return {
            'x': float(self.state[0]),
            'y': float(self.state[1]),
            'vx': float(self.state[2]),
            'vy': float(self.state[3]),
            'speed': float(np.sqrt(self.state[2]**2 + self.state[3]**2))
        }


def create_tracker(algorithm='KF'):
    """工厂函数"""
    if algorithm == 'KF':
        from advanced_tracker import KFTracker
        return KFTracker(dt=1.0, q=0.08, r=0.8)
    elif algorithm == 'EKF':
        from advanced_tracker import EKFTracker
        return EKFTracker(dt=1.0, q=0.08, r=0.8)
    elif algorithm == 'UKF':
        from advanced_tracker import UKFTracker
        return UKFTracker(dt=1.0, q=0.08, r=0.8)
    elif algorithm == 'PF':
        return OptimizedPFTracker(num_particles=300, process_noise=0.3, measurement_noise=1.5)
    else:
        raise ValueError(f"不支持: {algorithm}")


if __name__ == '__main__':
    print("=" * 50)
    print("优化版粒子滤波测试")
    print("=" * 50)
    
    tracker = OptimizedPFTracker(num_particles=300)
    
    errors = []
    x = y = 0
    vx, vy = 1.5, 0.5
    
    for i in range(100):
        x += vx
        y += vy
        
        # 测量噪声
        mx = x + np.random.randn() * 0.3
        my = y + np.random.randn() * 0.3
        
        ex, ey = tracker.process(mx, my)
        
        error = np.sqrt((ex - x)**2 + (ey - y)**2)
        errors.append(error)
    
    mean_error = np.mean(errors)
    print(f"优化PF误差: {mean_error:.4f}")
    print(f"误差标准差: {np.std(errors):.4f}")
    print(f"最大误差: {np.max(errors):.4f}")
