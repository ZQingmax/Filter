import numpy as np
from scipy import signal 
from typing import Tuple

# ===== 信号生成器 =====
class SignalGenerator:
    @staticmethod
    def generate_sine(f0: float, n: int, fs: float = 1.0, amplitude: float = 1.0):
        """生成正弦波信号"""
        t = np.arange(n) / fs
        xs = amplitude * np.sin(2 * np.pi * f0 * t)
        return xs, t
    
    @staticmethod
    def generate_square(f0: float, n: int, fs: float = 1.0, amplitude: float = 1.0):
        """生成方波信号"""
        t = np.arange(n) / fs
        xs = amplitude * np.sign(np.sin(2 * np.pi * f0 * t))
        return xs, t
    
    @staticmethod
    def generate_triangle(f0: float, n: int, fs: float = 1.0, amplitude: float = 1.0):
        """生成三角波信号"""
        t = np.arange(n) / fs
        xs = amplitude * (2/np.pi) * np.arcsin(np.sin(2 * np.pi * f0 * t))
        return xs, t
    
    @staticmethod
    def generate_chirp(f_start: float, f_end: float, n: int, fs: float = 1.0):
        """生成线性调频信号(chirp)"""
        t = np.arange(n) / fs
        beta = (f_end - f_start) / (n/fs)
        xs = np.sin(2 * np.pi * (f_start * t + 0.5 * beta * t**2))
        return xs, t

# ===== 噪声生成器 =====
class Noise:
    @staticmethod
    def add_awgn_noise(signal: np.ndarray, snr_db: float):
        """添加高斯白噪声"""
        signal_power = np.mean(signal**2)
        snr_linear = 10**(snr_db/10)
        noise_power = signal_power / snr_linear
        noise = np.random.normal(0, np.sqrt(noise_power), len(signal))
        return signal + noise
    
    @staticmethod
    def add_salt_pepper_noise(signal: np.ndarray, noise_prob: float = 0.1):
        """添加椒盐噪声"""
        noisy_signal = signal.copy()
        mask = np.random.random(len(signal)) < noise_prob
        salt_pepper = np.random.choice([-1, 1], size=np.sum(mask))
        noisy_signal[mask] += salt_pepper * np.max(np.abs(signal))
        return noisy_signal
    
    @staticmethod
    def add_uniform_noise(signal: np.ndarray, amplitude: float = 0.5):
        """添加均匀分布噪声"""
        noise = np.random.uniform(-amplitude, amplitude, len(signal))
        return signal + noise

