import numpy as np
from scipy import signal 
from typing import Tuple

# ------------------------------
# 信号生成类
# ------------------------------
class SignalGenerator:
    @staticmethod
    def generate_sine(f0: float, n: int, fs: float = 1.0) -> np.ndarray:
        """生成正弦波"""
        t = np.arange(n) / fs
        return np.sin(2 * np.pi * f0 * t), t

    @staticmethod
    def generate_square(f0: float, n: int, fs: float = 1.0) -> np.ndarray:
        """生成方波"""
        t = np.arange(n) / fs
        return signal.square(2 * np.pi * f0 * t), t

    @staticmethod
    def generate_triangle(f0: float, n: int, fs: float = 1.0) -> np.ndarray:
        """生成对称三角波"""
        t = np.arange(n) / fs
        return signal.sawtooth(2 * np.pi * f0 * t, width=0.5), t
# ------------------------------
# 噪声生成类
# ------------------------------
class Noise:
    @staticmethod
    def add_awgn_noise(x: np.ndarray, snr_db: float) -> np.ndarray:
        """给输入信号添加加性高斯白噪声 (AWGN)"""
        snr_linear = 10 ** (snr_db / 10.0)
        x_power = np.mean(np.abs(x) ** 2)
        noise_power = x_power / snr_linear
        if np.iscomplexobj(x):
            noise = (np.random.randn(len(x)) + 1j * np.random.randn(len(x))) * np.sqrt(noise_power / 2)
        else:
            noise = np.random.randn(len(x)) * np.sqrt(noise_power)
        return x + noise

    @staticmethod
    def add_salt_pepper_noise(x: np.ndarray, noise_prob: float) -> np.ndarray:
        """添加椒盐噪声"""
        noisy_x = x.copy()
        noise_pos = np.random.random(len(x)) < noise_prob
        salt = noise_pos & (np.random.random(len(x)) < 0.5)
        pepper = noise_pos & ~salt
        noisy_x[salt] = np.max(x)
        noisy_x[pepper] = np.min(x)
        return noisy_x

    @staticmethod
    def add_uniform_noise(x: np.ndarray, amplitude: float) -> np.ndarray:
        """添加均匀分布噪声"""
        noise = np.random.uniform(-amplitude, amplitude, len(x))
        return x + noise

