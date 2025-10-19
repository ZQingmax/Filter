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
    
    def filter(self, x, d):
        """
        Filter entire signal sequence
        
        Parameters:
        x: array - Input signal
        d: array - Desired signal
        
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
            y[n] = self.update(x_buffer, d[n])
            e[n] = d[n] - y[n]
        
        return y, e


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
    
    # Error signal
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
    np.random.seed(20)
    
    # Parameters
    N = 1000              # Signal length
    M = 32                # Filter length
    noise_power = 0.5     # Noise power
    sigma_n_squared = noise_power  # Observation noise variance
    sigma_d_squared = 0   # Parameter diffusion variance (0 for stationary)
    
    print("概率最小均方(PLMS)算法演示")
    print("基于 Fernández-Bes et al. 的论文实现")
    print("=" * 60)
    print(f"信号长度: {N}")
    print(f"滤波器长度 M: {M}")
    print(f"观测噪声方差 σ²_n: {sigma_n_squared}")
    print(f"参数扩散方差 σ²_d: {sigma_d_squared}")
    print(f"噪声功率: {noise_power}")
    print("=" * 60)
    
    # Generate signals
    t, original, noisy, noise = generate_signals(N, noise_power, noise_type='impulsive')
    
    # Create PLMS filter
    plms = ProbabilisticLMS(M, sigma_n_squared, sigma_d_squared)
    
    # Apply filter
    # Use original signal as desired signal for demonstration
    filtered, error = plms.filter(noisy, original)
    
    # Calculate performance metrics
    calculate_metrics(original, noisy, filtered)
    
    # Plot results
    print("\n生成图表...")
    plot_results(t, original, noisy, filtered)
    plot_comparison(t, original, noisy, filtered)
    plot_learning_curves(plms, error)
    
    # Print final adaptive parameters
    print("\n最终自适应参数:")
    print(f"最终步长 η: {plms.eta_history[-1]:.6f}")
    print(f"最终不确定性 σ²: {plms.sigma_history[-1]:.6f}")
    print("=" * 60)