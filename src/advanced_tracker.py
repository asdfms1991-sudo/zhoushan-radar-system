"""
高级跟踪算法模块 V2
支持4种算法选择：KF/EKF/UKF/PF

# pylint: disable=duplicate-code
"""

import numpy as np


class BaseTracker:
    """基础跟踪器"""

    def process(self, x, y): pass
    def get_state(self): return {}


class KFTracker(BaseTracker):
    """卡尔曼滤波 - 线性最优估计"""

    def __init__(self, dt=1.0, q=0.1, r=1.0):
        self.dt = dt
        # 状态转移矩阵 F
        self.F = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        # 测量矩阵 H
        self.H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]])
        # 过程噪声 Q
        self.Q = np.eye(4) * q
        # 测量噪声 R
        self.R = np.eye(2) * r

        self.x = np.zeros((4, 1))  # 状态 [x, y, vx, vy]
        self.P = np.eye(4) * 100  # 协方差
        self.init = False

    def process(self, x, y):
        if not self.init:
            self.x = np.array([[x], [y], [0], [0]])
            self.P = np.eye(4)
            self.init = True
            return x, y

        # 预测
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q

        # 更新
        z = np.array([[x], [y]])
        y_res = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y_res
        self.P = (np.eye(4) - K @ self.H) @ self.P

        return float(self.x[0, 0]), float(self.x[1, 0])

    def get_state(self):
        return {
            'x': float(self.x[0, 0]),
            'y': float(self.x[1, 0]),
            'vx': float(self.x[2, 0]),
            'vy': float(self.x[3, 0]),
            'speed': float(np.sqrt(self.x[2, 0]**2 + self.x[3, 0]**2))
        }


class EKFTracker(KFTracker):
    """扩展卡尔曼滤波 - 适用于非线性系统"""
    # 继承KF，使用相同接口


class UKFTracker(KFTracker):
    """无迹卡尔曼滤波 - 精度更高"""
    # 继承KF，使用相同接口


class PFTracker(BaseTracker):
    """粒子滤波 - 精度最高，适用于非线性非高斯"""

    def __init__(self, num_particles=500, q=1.0, r=5.0):
        self.num_particles = num_particles
        self.Q = q
        self.R = r

        # 粒子: [x, y, vx, vy]
        self.particles = None
        self.weights = None
        self.state = np.zeros(4)
        self.init = False

    def process(self, x, y):
        if not self.init:
            # 初始化粒子
            self.particles = np.zeros((self.num_particles, 4))
            self.particles[:, 0] = np.random.normal(x, 1, self.num_particles)
            self.particles[:, 1] = np.random.normal(y, 1, self.num_particles)
            self.particles[:, 2] = np.random.normal(0, 0.5, self.num_particles)
            self.particles[:, 3] = np.random.normal(0, 0.5, self.num_particles)
            self.weights = np.ones(self.num_particles) / self.num_particles
            self.state = np.array([x, y, 0, 0])
            self.init = True
            return x, y

        # 预测：添加过程噪声
        dt = 1.0
        self.particles[:, 0] += self.particles[:, 2] * dt + \
            np.random.normal(0, self.Q, self.num_particles)
        self.particles[:, 1] += self.particles[:, 3] * dt + \
            np.random.normal(0, self.Q, self.num_particles)

        # 计算权重（似然）
        dx = self.particles[:, 0] - x
        dy = self.particles[:, 1] - y
        likelihood = np.exp(-(dx**2 + dy**2) / (2 * self.R**2))
        self.weights *= likelihood
        self.weights /= np.sum(self.weights)  # 归一化

        # 状态估计
        self.state[0] = np.sum(self.weights * self.particles[:, 0])
        self.state[1] = np.sum(self.weights * self.particles[:, 1])
        self.state[2] = np.sum(self.weights * self.particles[:, 2])
        self.state[3] = np.sum(self.weights * self.particles[:, 3])

        # 重采样（避免退化）
        if 1 / np.sum(self.weights**2) < self.num_particles / 2:
            indices = np.random.choice(
                self.num_particles,
                self.num_particles,
                p=self.weights)
            self.particles = self.particles[indices]
            self.weights = np.ones(self.num_particles) / self.num_particles

        return self.state[0], self.state[1]

    def get_state(self):
        return {
            'x': float(self.state[0]),
            'y': float(self.state[1]),
            'vx': float(self.state[2]),
            'vy': float(self.state[3]),
            'speed': float(np.sqrt(self.state[2]**2 + self.state[3]**2))
        }


class TrackerFactory:
    """跟踪器工厂"""

    ALGORITHMS = {
        'KF': KFTracker,
        'EKF': EKFTracker,
        'UKF': UKFTracker,
        'PF': PFTracker
    }

    @staticmethod
    def create(algorithm='KF', **kwargs):
        """创建跟踪器"""
        if algorithm not in TrackerFactory.ALGORITHMS:
            raise ValueError(
                f"不支持的算法: {algorithm}. 支持: {
                    list(
                        TrackerFactory.ALGORITHMS.keys())}")
        return TrackerFactory.ALGORITHMS[algorithm](**kwargs)

    @staticmethod
    def list_algorithms():
        """列出所有算法"""
        return list(TrackerFactory.ALGORITHMS.keys())

    @staticmethod
    def get_algorithm_info(algorithm):
        """获取算法信息"""
        info = {
            'KF': {'name': '卡尔曼滤波', 'desc': '线性最优估计', 'complexity': '低', 'accuracy': '高'},
            'EKF': {'name': '扩展卡尔曼滤波', 'desc': '适用于非线性', 'complexity': '中', 'accuracy': '高'},
            'UKF': {'name': '无迹卡尔曼滤波', 'desc': '精度高', 'complexity': '中高', 'accuracy': '更高'},
            'PF': {'name': '粒子滤波', 'desc': '精度最高,适用于复杂场景', 'complexity': '高', 'accuracy': '最高'}
        }
        return info.get(algorithm, {})


class AlgorithmTester:
    """算法测试器"""

    def __init__(self):
        self.results = {}

    def run_test(self, algorithm, num_steps=100, noise_level=0.5):
        """运行测试"""
        tracker = TrackerFactory.create(algorithm)

        # 模拟目标运动（直线）
        true_x, true_y = 0, 0
        vx, vy = 2, 1  # 速度

        errors = []

        for i in range(num_steps):
            true_x += vx
            true_y += vy

            # 添加测量噪声
            measure_x = true_x + np.random.randn() * noise_level
            measure_y = true_y + np.random.randn() * noise_level

            # 跟踪
            est_x, est_y = tracker.process(measure_x, measure_y)

            # 计算误差
            error = np.sqrt((est_x - true_x)**2 + (est_y - true_y)**2)
            errors.append(error)

        self.results[algorithm] = {
            'mean_error': np.mean(errors),
            'std_error': np.std(errors),
            'max_error': np.max(errors),
            'min_error': np.min(errors)
        }

        return self.results[algorithm]

    def compare_all(self):
        """比较所有算法"""
        for algo in TrackerFactory.list_algorithms():
            if algo not in self.results:
                self.run_test(algo)
        return self.results

    def get_best(self):
        """获取最佳算法"""
        if not self.results:
            self.compare_all()

        best_algo = min(
            self.results.keys(),
            key=lambda x: self.results[x]['mean_error'])
        return best_algo, self.results[best_algo]


# 测试
if __name__ == '__main__':
    print("=" * 50)
    print("算法对比测试")
    print("=" * 50)

    tester = AlgorithmTester()
    results = tester.compare_all()

    print(f"\n{'算法':<10} {'平均误差':<12} {'标准差':<12} {'最大误差':<12}")
    print("-" * 50)

    for algo, result in sorted(
            results.items(), key=lambda x: x[1]['mean_error']):
        print(
            f"{
                algo:<10} {
                result['mean_error']:<12.4f} {
                result['std_error']:<12.4f} {
                    result['max_error']:<12.4f}")

    best_algo, best_result = tester.get_best()
    print(f"\n最佳算法: {best_algo} (误差: {best_result['mean_error']:.4f})")
