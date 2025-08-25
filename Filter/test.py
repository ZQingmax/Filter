import numpy as np
import matplotlib.pyplot as plt
from Signal import Noise, SignalGenerator
from plotter import Plotter
from LMS_Algorithm import lms
from KLMS_Algorithm import klms
from NLMS_Algorithm import nlms

if __name__ == '__main__':
    fs = 1        # 采样频率
    f0 = 0.02     # 信号频率
    n = 1000      # 信号长度
    # 生成原始信号
    xs, t = SignalGenerator.generate_sine(f0, n)  # 正弦波
    # xs, t = SignalGenerator.generate_square(f0, n)  # 方波
    # xs, t = SignalGenerator.generate_triangle(f0, n)  # 三角波
    
    # 使用高斯噪声
    ws = Noise.add_awgn_noise(xs, 20) 
    # # 使用椒盐噪声
    #ws = Noise().add_salt_pepper_noise(xs, noise_prob=0.1)  
    # 或使用均匀分布噪声
    #ws = Noise().add_uniform_noise(xs, amplitude=0.5)

    #lms 处理
    #yn, W, en = lms(ws, xs, M = 20, mu = 0.001)

    # KLMS 处理
    # x = ws.reshape(-1, 1)   # 输入 (N,1)
    # d = xs                  # 期望信号
    # yn, en = klms(x, d, mu = 0.5, sigma=1.0)

    # NLMS 处理
    yn, en, w_hist = nlms(ws, xs, mu = 0.05, L = 20)

    # 绘图
    p = Plotter()
    p.plot_signals(t, xs, ws, yn, en)