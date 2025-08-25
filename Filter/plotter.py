import matplotlib.pyplot as plt

class Plotter:
    def __init__(self):
        # 设置中文字体和负号
        plt.rcParams['font.sans-serif'] = ['SimHei']   # 黑体
        plt.rcParams['axes.unicode_minus'] = False

    @staticmethod
    def plot_signals(t, original, noisy, filtered, error):
        """
        1. 原始信号
        2. 加噪信号
        3. LMS滤波输出
        4. 误差信号
        """
        fig, axs = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
        
        # 原始信号
        axs[0].plot(t, original, color='blue')
        axs[0].set_ylabel("幅度")
        axs[0].set_title("原始信号")
        axs[0].grid(True)
        
        # 加噪信号
        axs[1].plot(t, noisy, color='blue')
        axs[1].set_ylabel("幅度")
        axs[1].set_title("加噪信号")
        axs[1].grid(True)
        
        # 滤波输出
        axs[2].plot(t, filtered, color='blue')
        axs[2].set_ylabel("幅度")
        axs[2].set_title("滤波输出")
        axs[2].grid(True)
        
        # 误差信号
        axs[3].plot(error, color='orange')
        axs[3].set_xlabel("时间（采样点）")
        axs[3].set_ylabel("幅度")
        axs[3].set_title("误差信号 e(n)")
        axs[3].grid(True)
        
        plt.tight_layout()
        plt.show()
