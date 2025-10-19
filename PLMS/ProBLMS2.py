import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置中文字体支持
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False

class ProbabilisticLMS:
    """
    Probabilistic Least-Mean-Squares Filter Implementation
    Based on "A Probabilistic Least-Mean-Squares Filter" by Fernández-Bes et al.
    """
    
    def __init__(self, M, sigma_n_squared, sigma_d_squared=0.0):
        """
        Initialize Probabilistic LMS filter
        
        Parameters:
        M: int - Filter length (number of parameters)
        sigma_n_squared: float - Observation noise variance
        sigma_d_squared: float - Parameter diffusion variance (0 for stationary)
        """
        self.M = M
        self.sigma_n_squared = sigma_n_squared
        self.sigma_d_squared = sigma_d_squared
        
        # Initialize parameters
        self.w = np.zeros(M)  # Parameter vector
        self.sigma_k_squared = 1.0  # Uncertainty estimate
        
        # For tracking performance
        self.msd_history = []
        self.sigma_history = []
        self.eta_history = []
        
    def update(self, x_k, y_k, w_true=None):
        """
        Update filter with new input-output pair
        
        Parameters:
        x_k: array - Input regression vector
        y_k: float - Desired output
        w_true: array - True parameter vector (for MSD calculation)
        
        Returns:
        y_pred: float - Predicted output
        """
        # Prediction
        y_pred = np.dot(x_k.T, self.w)
        error = y_k - y_pred
        
        # Compute adaptive step size (equation 7 in paper)
        x_norm_squared = np.dot(x_k, x_k)
        eta_k = (self.sigma_k_squared + self.sigma_d_squared) / \
                ((self.sigma_k_squared + self.sigma_d_squared) * x_norm_squared + self.sigma_n_squared)
        
        # Update parameter estimate (equation 11)
        self.w = self.w + eta_k * error * x_k
        
        # Update uncertainty estimate (equation 10)
        self.sigma_k_squared = (1 - eta_k * x_norm_squared / self.M) * \
                               (self.sigma_k_squared + self.sigma_d_squared)
        
        # Store history for analysis
        if w_true is not None:
            msd = np.mean((w_true - self.w)**2)
            self.msd_history.append(msd)
        
        self.sigma_history.append(self.sigma_k_squared)
        self.eta_history.append(eta_k)
        
        return y_pred
    
    def filter(self, x, d, w_true=None):
        """
        Filter entire signal sequence
        
        Parameters:
        x: array - Input signal
        d: array - Desired signal
        w_true: array - True system coefficients (optional, for MSD calculation)
        
        Returns:
        y: array - Output signal
        e: array - Error signal
        """
        N = len(x)
        y = np.zeros(N)
        e = np.zeros(N)
        
        # Input buffer
        x_buffer = np.zeros(self.M)
        
        for n in range(N):
            # Update input buffer
            x_buffer = np.roll(x_buffer, 1)
            x_buffer[0] = x[n]
            
            # Update filter
            y[n] = self.update(x_buffer, d[n], w_true)
            e[n] = d[n] - y[n]
        
        return y, e


def generate_system_identification_data(N=1000, M=32, noise_power=0.5, 
                                        noise_type='impulsive', impulse_prob=0.1, 
                                        impulse_amplitude=5.0):
    """
    生成系统辨识数据（用于计算MSD）
    
    Parameters:
    N: int - Signal length
    M: int - System/filter length
    noise_power: float - Base noise power
    noise_type: str - 'gaussian', 'impulsive', or 'mixed'
    impulse_prob: float - Probability of impulse occurrence
    impulse_amplitude: float - Amplitude of impulses
    
    Returns:
    x: array - Input signal
    d: array - Desired output (with noise)
    w_true: array - True system coefficients
    noise: array - Noise signal
    """
    # 生成真实系统系数 (unknown system)
    w_true = np.random.randn(M) * 0.5
    w_true = w_true / np.linalg.norm(w_true)  # 归一化到单位范数
    
    # 生成输入信号（白噪声）
    x = np.random.randn(N)
    
    # 通过真实系统生成期望输出
    d_clean = np.zeros(N)
    x_buffer = np.zeros(M)
    
    for n in range(N):
        x_buffer = np.roll(x_buffer, 1)
        x_buffer[0] = x[n]
        d_clean[n] = np.dot(w_true, x_buffer)
    
    # 添加噪声
    if noise_type == 'gaussian':
        noise = np.random.normal(0, np.sqrt(noise_power), N)
        
    elif noise_type == 'impulsive':
        noise = np.random.normal(0, np.sqrt(noise_power * 0.1), N)
        impulse_locations = np.random.rand(N) < impulse_prob
        impulse_values = np.random.choice([-1, 1], N) * impulse_amplitude
        noise[impulse_locations] += impulse_values[impulse_locations]
        
    elif noise_type == 'mixed':
        noise = np.random.normal(0, np.sqrt(noise_power), N)
        impulse_locations = np.random.rand(N) < impulse_prob
        impulse_values = np.random.choice([-1, 1], N) * impulse_amplitude
        noise[impulse_locations] += impulse_values[impulse_locations]
        
    else:
        raise ValueError("noise_type must be 'gaussian', 'impulsive', or 'mixed'")
    
    d = d_clean + noise
    
    return x, d, w_true, noise


def generate_signals(N=1000, noise_power=0.5, noise_type='impulsive', impulse_prob=0.1, impulse_amplitude=5.0):
    """
    生成测试信号（支持高斯和非高斯噪声）
    
    Parameters:
    N: int - Signal length
    noise_power: float - Base noise power
    noise_type: str - 'gaussian', 'impulsive', or 'mixed'
    impulse_prob: float - Probability of impulse occurrence (for impulsive noise)
    impulse_amplitude: float - Amplitude of impulses (relative to signal)
    
    Returns:
    t: array - Time vector
    original: array - Clean original signal
    noisy: array - Noisy signal
    noise: array - Noise
    """
    t = np.arange(N)
    
    # Generate original signal: combination of sinusoids
    f1, f2, f3 = 0.02, 0.05, 0.08
    original = (np.sin(2 * np.pi * f1 * t) + 
                0.5 * np.sin(2 * np.pi * f2 * t) +
                0.3 * np.sin(2 * np.pi * f3 * t))
    
    if noise_type == 'gaussian':
        # 纯高斯噪声
        noise = np.random.normal(0, np.sqrt(noise_power), N)
        
    elif noise_type == 'impulsive':
        # 脉冲噪声 (Salt-and-Pepper + Gaussian base)
        noise = np.random.normal(0, np.sqrt(noise_power * 0.1), N)  # 小的高斯基底
        impulse_locations = np.random.rand(N) < impulse_prob
        impulse_values = np.random.choice([-1, 1], N) * impulse_amplitude
        noise[impulse_locations] += impulse_values[impulse_locations]
        
    elif noise_type == 'mixed':
        # 混合噪声：高斯 + 偶发脉冲
        noise = np.random.normal(0, np.sqrt(noise_power), N)
        impulse_locations = np.random.rand(N) < impulse_prob
        impulse_values = np.random.choice([-1, 1], N) * impulse_amplitude
        noise[impulse_locations] += impulse_values[impulse_locations]
        
    else:
        raise ValueError("noise_type must be 'gaussian', 'impulsive', or 'mixed'")
    
    noisy = original + noise
    
    return t, original, noisy, noise


def plot_results(t, original, noisy, filtered):
    """
    Plot comparison of three signals
    
    Parameters:
    t: array - Time vector
    original: array - Original signal
    noisy: array - Noisy signal
    filtered: array - Filtered signal
    """
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # Original signal
    axes[0].plot(t, original, 'g-', linewidth=1.5, label='原始信号')
    axes[0].set_title('原始干净信号', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('样本点')
    axes[0].set_ylabel('幅度')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()
    
    # Noisy signal
    axes[1].plot(t, noisy, 'r-', linewidth=0.8, alpha=0.7, label='加噪信号')
    axes[1].set_title('加噪声后的信号', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('样本点')
    axes[1].set_ylabel('幅度')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    
    # Filtered signal
    axes[2].plot(t, filtered, 'b-', linewidth=1.5, label='PLMS滤波信号')
    axes[2].plot(t, original, 'g--', linewidth=1, alpha=0.5, label='原始信号(参考)')
    axes[2].set_title('PLMS滤波后的信号', fontsize=14, fontweight='bold')
    axes[2].set_xlabel('样本点')
    axes[2].set_ylabel('幅度')
    axes[2].grid(True, alpha=0.3)
    axes[2].legend()
    
    plt.tight_layout()
    plt.show()


def plot_comparison(t, original, noisy, filtered):
    """
    Plot all signals in one figure for comparison
    """
    plt.figure(figsize=(14, 6))
    
    plt.plot(t, original, 'g-', linewidth=2, label='原始信号', alpha=0.8)
    plt.plot(t, noisy, 'r-', linewidth=0.5, alpha=0.4, label='加噪信号')
    plt.plot(t, filtered, 'b-', linewidth=1.5, label='PLMS滤波信号', alpha=0.9)
    
    plt.title('信号对比：原始 vs 加噪 vs PLMS滤波', fontsize=16, fontweight='bold')
    plt.xlabel('样本点', fontsize=12)
    plt.ylabel('幅度', fontsize=12)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def plot_learning_curves(plms, error):
    """
    Plot learning curves and adaptive parameters
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # MSD curve (if available) or Error signal
    if len(plms.msd_history) > 0:
        msd_db = 10 * np.log10(np.array(plms.msd_history) + 1e-12)
        axes[0, 0].plot(msd_db, 'b-', linewidth=1.5)
        axes[0, 0].set_title('均方偏差 (MSD) 学习曲线', fontsize=12, fontweight='bold')
        axes[0, 0].set_xlabel('样本点')
        axes[0, 0].set_ylabel('MSD (dB)')
        axes[0, 0].grid(True, alpha=0.3)
    else:
        axes[0, 0].plot(np.abs(error), 'b-', linewidth=1)
        axes[0, 0].set_title('误差信号的绝对值', fontsize=12, fontweight='bold')
        axes[0, 0].set_xlabel('样本点')
        axes[0, 0].set_ylabel('|误差|')
        axes[0, 0].grid(True, alpha=0.3)
    
    # Cumulative MSE
    N = len(error)
    mse_curve = np.cumsum(error**2) / (np.arange(N) + 1)
    axes[0, 1].plot(mse_curve, 'r-', linewidth=1.5)
    axes[0, 1].set_title('累积均方误差', fontsize=12, fontweight='bold')
    axes[0, 1].set_xlabel('样本点')
    axes[0, 1].set_ylabel('MSE')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Step size (eta) evolution
    axes[1, 0].plot(plms.eta_history, 'g-', linewidth=1)
    axes[1, 0].set_title('自适应步长 η(k) 演化', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('样本点')
    axes[1, 0].set_ylabel('步长 η')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Uncertainty (sigma) evolution
    axes[1, 1].plot(plms.sigma_history, 'm-', linewidth=1.5)
    axes[1, 1].set_title('不确定性估计 σ²(k) 演化', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('样本点')
    axes[1, 1].set_ylabel('不确定性 σ²')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def plot_coefficient_comparison(w_true, w_est):
    """
    Plot comparison between true and estimated coefficients
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Coefficient comparison
    indices = np.arange(len(w_true))
    axes[0].stem(indices, w_true, linefmt='g-', markerfmt='go', basefmt='k-', label='真实系数')
    axes[0].stem(indices, w_est, linefmt='b-', markerfmt='bs', basefmt='k-', label='估计系数')
    axes[0].set_title('系数对比：真实 vs 估计', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('系数索引')
    axes[0].set_ylabel('系数值')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Coefficient error
    error = w_true - w_est
    axes[1].bar(indices, error, color='r', alpha=0.7)
    axes[1].set_title('系数误差分布', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('系数索引')
    axes[1].set_ylabel('误差 (真实 - 估计)')
    axes[1].grid(True, alpha=0.3, axis='y')
    axes[1].axhline(y=0, color='k', linestyle='-', linewidth=0.8)
    
    plt.tight_layout()
    plt.show()


def calculate_metrics(original, noisy, filtered):
    """
    Calculate performance metrics
    """
    # SNR improvement
    mse_noisy = np.mean((original - noisy) ** 2)
    mse_filtered = np.mean((original - filtered) ** 2)
    
    snr_input = 10 * np.log10(np.var(original) / mse_noisy)
    snr_output = 10 * np.log10(np.var(original) / mse_filtered)
    
    print("=" * 60)
    print("性能评估指标")
    print("=" * 60)
    print(f"输入信噪比 (SNR): {snr_input:.2f} dB")
    print(f"输出信噪比 (SNR): {snr_output:.2f} dB")
    print(f"信噪比改善: {snr_output - snr_input:.2f} dB")
    print(f"输入均方误差 (MSE): {mse_noisy:.6f}")
    print(f"输出均方误差 (MSE): {mse_filtered:.6f}")
    print(f"MSE降低: {(1 - mse_filtered/mse_noisy)*100:.2f}%")
    print("=" * 60)


# Main program
if __name__ == "__main__":
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Parameters
    N = 2000              # Signal length (增加到2000以更好观察收敛)
    M = 32                # Filter length
    noise_power = 0.5     # Noise power
    
    # 噪声参数
    noise_type = 'impulsive'  # 'gaussian', 'impulsive', or 'mixed'
    impulse_prob = 0.05       # 5% 的样本点出现脉冲
    impulse_amplitude = 8.0   # 脉冲幅度
    
    sigma_n_squared = noise_power  # Observation noise variance
    sigma_d_squared = 1e-6   # Parameter diffusion variance (0 for stationary)
    
    print("=" * 70)
    print("概率最小均方(PLMS)算法演示 - 系统辨识与MSD测试")
    print("基于 Fernández-Bes et al. 的论文实现")
    print("=" * 70)
    
    # 选择运行模式
    print("\n请选择运行模式:")
    print("1 - 信号去噪模式 (Signal Denoising)")
    print("2 - 系统辨识模式 (System Identification with MSD)")
    mode = input("输入选项 [1/2]: ").strip()
    
    if mode == '2':
        # ========== 系统辨识模式 (计算MSD) ==========
        print("\n" + "=" * 70)
        print(">>> 系统辨识模式 (System Identification Mode) <<<")
        print("=" * 70)
        print(f"信号长度: {N}")
        print(f"滤波器长度 M: {M}")
        print(f"噪声类型: {noise_type.upper()}")
        if noise_type in ['impulsive', 'mixed']:
            print(f"脉冲概率: {impulse_prob*100:.1f}%")
            print(f"脉冲幅度: ±{impulse_amplitude}")
        print(f"观测噪声方差 σ²_n: {sigma_n_squared}")
        print(f"参数扩散方差 σ²_d: {sigma_d_squared}")
        print("=" * 70)
        
        # 生成系统辨识数据
        print("\n正在生成系统辨识数据...")
        x, d, w_true, noise = generate_system_identification_data(
            N, M, noise_power,
            noise_type=noise_type,
            impulse_prob=impulse_prob,
            impulse_amplitude=impulse_amplitude
        )
        
        print(f"真实系统系数范围: [{w_true.min():.4f}, {w_true.max():.4f}]")
        print(f"真实系数L2范数: {np.linalg.norm(w_true):.4f}")
        
        # 创建PLMS滤波器
        plms = ProbabilisticLMS(M, sigma_n_squared, sigma_d_squared)
        
        # 运行自适应滤波
        print("\n正在运行PLMS自适应滤波...")
        y, error = plms.filter(x, d, w_true)
        
        # 显示结果
        print("\n" + "=" * 70)
        print("系统辨识结果")
        print("=" * 70)
        final_msd = plms.msd_history[-1]
        final_msd_db = 10 * np.log10(final_msd + 1e-12)
        print(f"最终MSD (线性): {final_msd:.8f}")
        print(f"最终MSD (dB): {final_msd_db:.2f} dB")
        print(f"最终步长 η: {plms.eta_history[-1]:.6f}")
        print(f"最终不确定性 σ²: {plms.sigma_history[-1]:.6f}")
        print(f"系数估计误差范数: {np.linalg.norm(w_true - plms.w):.6f}")
        print(f"平均MSE: {np.mean(error**2):.6f}")
        print("=" * 70)
        
        # 绘制学习曲线
        print("\n生成学习曲线图...")
        plot_learning_curves(plms, error)
        
        # 绘制系数对比
        print("生成系数对比图...")
        plot_coefficient_comparison(w_true, plms.w)
        
        print("\n✓ 系统辨识测试完成!")
        
    else:
        # ========== 信号去噪模式 ==========
        print("\n" + "=" * 70)
        print(">>> 信号去噪模式 (Signal Denoising Mode) <<<")
        print("=" * 70)
        print(f"信号长度: {N}")
        print(f"滤波器长度 M: {M}")
        print(f"噪声类型: {noise_type.upper()}")
        if noise_type in ['impulsive', 'mixed']:
            print(f"脉冲概率: {impulse_prob*100:.1f}%")
            print(f"脉冲幅度: ±{impulse_amplitude}")
        print(f"观测噪声方差 σ²_n: {sigma_n_squared}")
        print(f"参数扩散方差 σ²_d: {sigma_d_squared}")
        print("=" * 70)
        
        # Generate signals
        print("\n正在生成测试信号...")
        t, original, noisy, noise = generate_signals(
            N, noise_power, 
            noise_type=noise_type,
            impulse_prob=impulse_prob,
            impulse_amplitude=impulse_amplitude
        )
        
        # Create PLMS filter
        plms = ProbabilisticLMS(M, sigma_n_squared, sigma_d_squared)
        
        # Apply filter
        print("正在运行PLMS滤波...")
        filtered, error = plms.filter(noisy, original)
        
        # Calculate performance metrics
        calculate_metrics(original, noisy, filtered)
        
        # Plot results
        print("\n生成信号对比图...")
        plot_results(t, original, noisy, filtered)
        plot_comparison(t, original, noisy, filtered)
        plot_learning_curves(plms, error)
        
        # Print final adaptive parameters
        print("\n最终自适应参数:")
        print(f"最终步长 η: {plms.eta_history[-1]:.6f}")
        print(f"最终不确定性 σ²: {plms.sigma_history[-1]:.6f}")
        print("=" * 70)
        
        print("\n✓ 信号去噪测试完成!")