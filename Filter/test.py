import numpy as np
import matplotlib.pyplot as plt
from scipy import signal  
from noise import Noise
from plotter import Plotter
from LMSAlgorithm import lmsFunc

if __name__ == '__main__':
    fs = 1  # 采样频率
    f0 = 0.02 # 信号频率
    n = 1000 # 信号长度
    t = np.arange(n) / fs  # 时间序列
    # 1. 正弦波
    xs_sin = np.sin(2 * np.pi * f0 * t)
    # 2. 方波
    xs_square = signal.square(2 * np.pi * f0 * t)
    # 3. 三角波（锯齿波 duty=0.5 会变成对称三角波）
    xs_triangle = signal.sawtooth(2 * np.pi * f0 * t, 0.5)
    
    xs = xs_sin  # 原始信号
    # 加噪信号
    n = Noise()
    ws = n.add_awgn_noise(xs, 20) 
    # # 使用椒盐噪声
    # ws = add_salt_pepper_noise(xs, noise_prob=0.1)  
    # 或使用均匀分布噪声
    #ws = n.add_uniform_noise(xs, amplitude=0.5)
    M = 20
    mu = 0.001
    yn, W, en = lmsFunc(ws, xs, 20, 0.001)
    # 绘图
    p = Plotter()
    p.plot_signals(t, xs, ws, yn, en)