import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import lfilter
import seaborn as sns

# Set plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

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

class StandardLMS:
    """Standard LMS Algorithm for comparison"""
    
    def __init__(self, M, mu):
        self.M = M
        self.mu = mu  # Step size
        self.w = np.zeros(M)
        self.msd_history = []
        
    def update(self, x_k, y_k, w_true=None):
        y_pred = np.dot(x_k.T, self.w)
        error = y_k - y_pred
        self.w = self.w + self.mu * error * x_k
        
        if w_true is not None:
            msd = np.mean((w_true - self.w)**2)
            self.msd_history.append(msd)
            
        return y_pred

class NLMS:
    """Normalized LMS Algorithm"""
    
    def __init__(self, M, mu, epsilon=1e-6):
        self.M = M
        self.mu = mu
        self.epsilon = epsilon
        self.w = np.zeros(M)
        self.msd_history = []
        
    def update(self, x_k, y_k, w_true=None):
        y_pred = np.dot(x_k.T, self.w)
        error = y_k - y_pred
        x_norm_squared = np.dot(x_k, x_k)
        step_size = self.mu / (x_norm_squared + self.epsilon)
        self.w = self.w + step_size * error * x_k
        
        if w_true is not None:
            msd = np.mean((w_true - self.w)**2)
            self.msd_history.append(msd)
            
        return y_pred

class RLS:
    """Recursive Least Squares for comparison"""
    
    def __init__(self, M, forgetting_factor=1.0, epsilon=0.01):
        self.M = M
        self.lam = forgetting_factor
        self.w = np.zeros(M)
        self.P = np.eye(M) / epsilon  # Inverse correlation matrix
        self.msd_history = []
        
    def update(self, x_k, y_k, w_true=None):
        y_pred = np.dot(x_k.T, self.w)
        error = y_k - y_pred
        
        k = self.P @ x_k / (self.lam + x_k.T @ self.P @ x_k)
        self.w = self.w + k * error
        self.P = (self.P - np.outer(k, x_k.T @ self.P)) / self.lam
        
        if w_true is not None:
            msd = np.mean((w_true - self.w)**2)
            self.msd_history.append(msd)
            
        return y_pred

class VSSNLMS:
    """
    Variable Step-Size Normalized LMS Algorithm
    Based on Shin, Sayed, and Song (2004)
    """
    
    def __init__(self, M, mu_max=1.5, alpha=0.80, C=1, epsilon=1e-6):
        """
        Initialize VSS-NLMS filter
        
        Parameters:
        M: int - Filter length
        mu_max: float - Maximum step size
        alpha: float - Smoothing parameter (0 < alpha < 1)
        C: float - Regularization parameter
        epsilon: float - Small constant to avoid division by zero
        """
        self.M = M
        self.mu_max = mu_max
        self.alpha = alpha
        self.C = C
        self.epsilon = epsilon
        
        # Initialize parameters
        self.w = np.zeros(M)
        self.p_k = 0.0  # Smoothed error power estimate
        self.msd_history = []
        self.step_size_history = []

    def update(self, x_k, y_k, w_true=None):
        """Update filter with new input-output pair"""
        y_pred = np.dot(x_k.T, self.w)
        error = y_k - y_pred
        # Update smoothed error power estimate
        self.p_k = self.alpha * self.p_k + (1 - self.alpha) * error**2
        # Compute variable step size
        x_norm_squared = np.dot(x_k, x_k)
        mu_k = self.mu_max * (1 - np.exp(-self.C * self.p_k))
        # Normalize step size (NLMS-style)
        normalized_step_size = mu_k / (x_norm_squared + self.epsilon)
        # Update parameter vector
        self.w = self.w + normalized_step_size * error * x_k
  
        # Store history
        self.step_size_history.append(mu_k)
        
        if w_true is not None:
            msd = np.mean((w_true - self.w)**2)
            self.msd_history.append(msd)
            
        return y_pred

def simulate_stationary_experiment(M=50, N=6000, SNR_dB=20, num_runs=50):
    """
    Simulate stationary system identification experiment
    Reproduces Figure 1 from the paper
    """
    print("Running stationary experiment...")
    
    # Initialize results storage
    algorithms = ['LMS', 'NLMS', 'VSSNLMS', 'RLS', 'ProbLMS1', 'ProbLMS2']
    msd_results = {alg: np.zeros(N) for alg in algorithms}
    
    for run in range(num_runs):
        if run % 10 == 0:
            print(f"Run {run+1}/{num_runs}")
            
        # Generate true system
        w_true = np.random.uniform(-1, 1, M)
        w_true = w_true / np.linalg.norm(w_true)  # Normalize
        
        # Calculate noise variance for desired SNR
        signal_power = 1.0  # Since ||w_true|| = 1 and E[||x||^2] = M
        noise_power = signal_power / (10**(SNR_dB/10))
        sigma_n_squared = noise_power
        
        # Initialize algorithms
        filters = {
            'LMS': StandardLMS(M, mu=0.01),
            'NLMS': NLMS(M, mu=0.5),
            'VSSNLMS': VSSNLMS(M, mu_max=2.0, alpha=0.80, C=1),
            'RLS': RLS(M, forgetting_factor=1.0, epsilon=0.01),
            'ProbLMS1': ProbabilisticLMS(M, sigma_n_squared),  # Perfect knowledge
            'ProbLMS2': ProbabilisticLMS(M, sigma_n_squared / 100)  # Suboptimal
        }
        
        for k in range(N):
            # Generate input and output
            x_k = np.random.randn(M)
            noise = np.sqrt(sigma_n_squared) * np.random.randn()
            y_k = np.dot(x_k.T, w_true) + noise
            
            # Update all filters
            for alg_name, filt in filters.items():
                filt.update(x_k, y_k, w_true)
                
        # Accumulate MSD results
        for alg_name in algorithms:
            msd_results[alg_name] += np.array(filters[alg_name].msd_history)
    
    # Average over runs
    for alg_name in algorithms:
        msd_results[alg_name] /= num_runs

    for alg_name, msd in msd_results.items():
      print(alg_name, msd.mean(), msd.min(), msd.max())
    
    return msd_results

def simulate_tracking_experiment(M=10, N=2000, SNR_dB=20):
    """
    Simulate tracking experiment with time-varying system
    """
    print("Running tracking experiment...")
    
    # System parameters
    signal_power = 1.0
    noise_power = signal_power / (10**(SNR_dB/10))
    sigma_n_squared = noise_power
    sigma_d_squared = 1e-6  # Small parameter variation
    
    # Initialize algorithms
    filters = {
        'LMS': StandardLMS(M, mu=0.01),
        'NLMS': NLMS(M, mu=0.5),
        'VSSNLMS': VSSNLMS(M, mu_max=2.0, alpha=0.80, C=1),
        'RLS': RLS(M, forgetting_factor=0.999),
        'ProbLMS': ProbabilisticLMS(M, sigma_n_squared, sigma_d_squared)
    }
    
    # Generate time-varying system
    w_true = np.zeros((N, M))
    w_true[0] = np.random.randn(M) * 0.5
    
    for k in range(1, N):
        # Random walk model for parameters
        w_true[k] = w_true[k-1] + np.sqrt(sigma_d_squared) * np.random.randn(M)
    
    # Run simulation
    results = {name: {'msd': [], 'predictions': []} for name in filters.keys()}
    y_true = []
    
    for k in range(N):
        # Generate input and output
        x_k = np.random.randn(M)
        noise = np.sqrt(sigma_n_squared) * np.random.randn()
        y_k = np.dot(x_k.T, w_true[k]) + noise
        y_true.append(y_k)
        
        # Update all filters
        for name, filt in filters.items():
            y_pred = filt.update(x_k, y_k, w_true[k])
            results[name]['predictions'].append(y_pred)
            if hasattr(filt, 'msd_history') and len(filt.msd_history) > 0:
                results[name]['msd'].append(filt.msd_history[-1])
    
    return results, y_true, w_true

def plot_stationary_results(msd_results):
    """Plot results for stationary experiment (robust: cycles colors/linestyles, explicit x-axis)."""
    plt.figure(figsize=(12, 8))
    
    colors = ['blue', 'green', 'cyan', 'red', 'orange', 'purple', 'magenta', 'brown']
    linestyles = ['-', '--', ':', '-.', '-', ':', '--', '-.']
    
    # 保证能处理不同长度的 msd 序列
    max_len = max(len(v) for v in msd_results.values())
    
    # 用于判断同名标签出现次数（确保图例唯一）
    keys_list = list(msd_results.keys())
    
    for i, (alg_name, msd) in enumerate(msd_results.items()):
        msd = np.asarray(msd)
        msd_db = 10 * np.log10(msd + 1e-15)  # Convert to dB, avoid log(0)
        x = np.arange(len(msd_db))
        
        color = colors[i % len(colors)]
        ls = linestyles[i % len(linestyles)]
        
        # 如果存在重复名字，给图例加上索引后缀，保证每条曲线都有标签
        if keys_list.count(alg_name) > 1:
            label = f"{alg_name} ({i})"
        else:
            label = alg_name
        
        plt.plot(x, msd_db, label=label, color=color, linestyle=ls, linewidth=2, alpha=0.95)

    plt.ylim(auto=True)
    plt.xlabel('Iterations')
    plt.ylabel('MSD (dB)')
    plt.title('Performance Comparison: Stationary Environment')
    plt.legend(loc='best', fontsize='small')
    plt.grid(True, alpha=0.3)
    plt.ylim([-60, -20])
    plt.xlim([0, max_len - 1])
    plt.tight_layout()
    plt.show()

def plot_tracking_results(results, y_true):
    """Plot results for tracking experiment"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot MSD comparison
    for name, data in results.items():
        if len(data['msd']) > 0:
            msd_db = 10 * np.log10(np.array(data['msd']) + 1e-15)
            ax1.plot(msd_db, label=name, linewidth=2)
    
    ax1.set_xlabel('Iterations')
    ax1.set_ylabel('MSD (dB)')
    ax1.set_title('Tracking Performance: Time-varying Environment')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot prediction comparison (first 500 samples)
    N_plot = min(500, len(y_true))
    time_axis = range(N_plot)
    
    ax2.plot(time_axis, y_true[:N_plot], 'k-', label='True output', linewidth=2, alpha=0.7)
    
    for name, data in results.items():
        if name == 'ProbLMS':  # Only plot ProbLMS prediction for clarity
            ax2.plot(time_axis, data['predictions'][:N_plot], 
                    '--', label=f'{name} prediction', linewidth=2)
    
    ax2.set_xlabel('Iterations')
    ax2.set_ylabel('Output')
    ax2.set_title('Output Prediction (First 500 samples)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def analyze_step_size_comparison():
    """Compare step size adaptation of different variable step-size algorithms"""
    print("\nComparing Step Size Adaptation Mechanisms...")
    
    M = 20
    N = 2000
    sigma_n_squared = 0.01
    sigma_d_squared = 1e-5
    
    # Initialize variable step-size algorithms
    prob_lms = ProbabilisticLMS(M, sigma_n_squared, sigma_d_squared)
    vss_nlms = VSSNLMS(M, mu_max=2.0, alpha=0.80, C=1)
    
    # Generate time-varying system
    w_true = np.random.randn(M) * 0.5
    
    # Add system change at midpoint
    change_point = N // 2
    
    for k in range(N):
        # Introduce a system change
        if k == change_point:
            w_true += np.random.randn(M) * 0.3  # Sudden change
            
        # Slow parameter drift
        w_true += np.sqrt(sigma_d_squared) * np.random.randn(M)
        
        # Generate input and output
        x_k = np.random.randn(M)
        y_k = np.dot(x_k.T, w_true) + np.sqrt(sigma_n_squared) * np.random.randn()
        
        # Update filters
        prob_lms.update(x_k, y_k, w_true)
        vss_nlms.update(x_k, y_k, w_true)
    
    # Plot comparison
    fig, axes = plt.subplots(3, 1, figsize=(12, 12))
    
    # Step size comparison
    axes[0].plot(prob_lms.eta_history, 'b-', label='ProbLMS η_k', linewidth=2)
    axes[0].plot(vss_nlms.step_size_history, 'r--', label='VSS-NLMS μ_k', linewidth=2)
    axes[0].axvline(x=change_point, color='k', linestyle=':', alpha=0.7, label='System change')
    axes[0].set_title('Step Size Evolution')
    axes[0].set_ylabel('Step Size')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # MSD comparison
    prob_msd_db = 10 * np.log10(np.array(prob_lms.msd_history) + 1e-15)
    vss_msd_db = 10 * np.log10(np.array(vss_nlms.msd_history) + 1e-15)
    
    axes[1].plot(prob_msd_db, 'b-', label='ProbLMS', linewidth=2)
    axes[1].plot(vss_msd_db, 'r--', label='VSS-NLMS', linewidth=2)
    axes[1].axvline(x=change_point, color='k', linestyle=':', alpha=0.7, label='System change')
    axes[1].set_title('Mean Square Deviation')
    axes[1].set_ylabel('MSD (dB)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    # Uncertainty evolution (ProbLMS only)
    axes[2].plot(prob_lms.sigma_history, 'g-', label='ProbLMS Uncertainty σ²_k', linewidth=2)
    axes[2].axvline(x=change_point, color='k', linestyle=':', alpha=0.7, label='System change')
    axes[2].set_title('Uncertainty Evolution (ProbLMS only)')
    axes[2].set_xlabel('Iterations')
    axes[2].set_ylabel('Uncertainty')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # Print final performance
    print(f"\nFinal Performance (last 200 samples):")
    print(f"ProbLMS MSD:    {prob_msd_db[-200:].mean():.2f} dB")
    print(f"VSS-NLMS MSD:   {vss_msd_db[-200:].mean():.2f} dB")
    
    return prob_lms, vss_nlms

def analyze_probabilistic_lms_properties():
    """Analyze key properties of Probabilistic LMS"""
    print("\nAnalyzing Probabilistic LMS Properties...")
    
    M = 20
    N = 1000
    sigma_n_squared = 0.01
    
    # Test different scenarios
    scenarios = {
        'Stationary': {'sigma_d_squared': 0.0},
        'Slow variation': {'sigma_d_squared': 1e-6},
        'Fast variation': {'sigma_d_squared': 1e-4}
    }
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    axes = axes.ravel()
    
    for i, (scenario_name, params) in enumerate(scenarios.items()):
        # Initialize filter
        prob_lms = ProbabilisticLMS(M, sigma_n_squared, params['sigma_d_squared'])
        
        # Generate data
        w_true = np.random.randn(M) * 0.5
        
        for k in range(N):
            if params['sigma_d_squared'] > 0:
                w_true += np.sqrt(params['sigma_d_squared']) * np.random.randn(M)
            
            x_k = np.random.randn(M)
            y_k = np.dot(x_k.T, w_true) + np.sqrt(sigma_n_squared) * np.random.randn()
            prob_lms.update(x_k, y_k, w_true)
        
        # Plot step size evolution
        axes[i].plot(prob_lms.eta_history, label='Step size η_k')
        axes[i].set_title(f'{scenario_name} Environment')
        axes[i].set_xlabel('Iterations')
        axes[i].set_ylabel('Step size')
        axes[i].grid(True, alpha=0.3)
        axes[i].legend()
    
    # Plot uncertainty evolution for stationary case
    prob_lms_stat = ProbabilisticLMS(M, sigma_n_squared, 0.0)
    w_true = np.random.randn(M) * 0.5
    
    for k in range(N):
        x_k = np.random.randn(M)
        y_k = np.dot(x_k.T, w_true) + np.sqrt(sigma_n_squared) * np.random.randn()
        prob_lms_stat.update(x_k, y_k, w_true)
    
    axes[3].plot(prob_lms_stat.sigma_history, 'r-', label='Uncertainty σ²_k')
    axes[3].set_title('Uncertainty Evolution (Stationary)')
    axes[3].set_xlabel('Iterations')
    axes[3].set_ylabel('Uncertainty')
    axes[3].grid(True, alpha=0.3)
    axes[3].legend()
    
    plt.tight_layout()
    plt.show()

def detailed_performance_analysis():
    """Detailed performance analysis with statistical metrics"""
    print("\nDetailed Performance Analysis...")
    
    M = 30
    N = 3000
    SNR_dB = 20
    num_runs = 30
    
    # Calculate noise variance
    signal_power = 1.0
    noise_power = signal_power / (10**(SNR_dB/10))
    sigma_n_squared = noise_power
    
    # Store results for statistical analysis
    final_msd_results = {
        'LMS': [],
        'NLMS': [],
        'VSSNLMS': [],
        'ProbLMS': []
    }
    
    convergence_times = {alg: [] for alg in final_msd_results.keys()}
    
    for run in range(num_runs):
        if run % 10 == 0:
            print(f"Analysis run {run+1}/{num_runs}")
            
        # Generate true system
        w_true = np.random.uniform(-1, 1, M)
        w_true = w_true / np.linalg.norm(w_true)
        
        # Initialize algorithms
        filters = {
            'LMS': StandardLMS(M, mu=0.01),
            'NLMS': NLMS(M, mu=0.5),
            'VSSNLMS': VSSNLMS(M, mu_max=1.0, alpha=0.95, C=1e-4),
            'ProbLMS': ProbabilisticLMS(M, sigma_n_squared)
        }
        
        # Run simulation
        for k in range(N):
            x_k = np.random.randn(M)
            noise = np.sqrt(sigma_n_squared) * np.random.randn()
            y_k = np.dot(x_k.T, w_true) + noise
            
            for alg_name, filt in filters.items():
                filt.update(x_k, y_k, w_true)
        
        # Calculate final MSD and convergence time
        for alg_name, filt in filters.items():
            # Final MSD (average of last 500 samples)
            final_msd = np.mean(filt.msd_history[-500:])
            final_msd_results[alg_name].append(final_msd)
            
            # Convergence time (when MSD drops below -35 dB)
            msd_db = 10 * np.log10(np.array(filt.msd_history) + 1e-15)
            converged_idx = np.where(msd_db < -35)[0]
            conv_time = converged_idx[0] if len(converged_idx) > 0 else N
            convergence_times[alg_name].append(conv_time)
    
    # Print statistical results
    print("\n=== Statistical Performance Analysis ===")
    print(f"Results based on {num_runs} Monte Carlo runs")
    print(f"System dimension: {M}, SNR: {SNR_dB} dB\n")
    
    print("Final MSD Performance (dB):")
    print(f"{'Algorithm':<12} {'Mean':<8} {'Std':<8} {'Min':<8} {'Max':<8}")
    print("-" * 50)
    
    for alg_name in final_msd_results.keys():
        msd_db_final = 10 * np.log10(np.array(final_msd_results[alg_name]))
        mean_msd = np.mean(msd_db_final)
        std_msd = np.std(msd_db_final)
        min_msd = np.min(msd_db_final)
        max_msd = np.max(msd_db_final)
        print(f"{alg_name:<12} {mean_msd:<8.2f} {std_msd:<8.2f} {min_msd:<8.2f} {max_msd:<8.2f}")
    
    print("\nConvergence Time Analysis (iterations to -35 dB):")
    print(f"{'Algorithm':<12} {'Mean':<8} {'Std':<8} {'Min':<8} {'Max':<8}")
    print("-" * 50)
    
    for alg_name in convergence_times.keys():
        conv_times = np.array(convergence_times[alg_name])
        mean_conv = np.mean(conv_times)
        std_conv = np.std(conv_times)
        min_conv = np.min(conv_times)
        max_conv = np.max(conv_times)
        print(f"{alg_name:<12} {mean_conv:<8.0f} {std_conv:<8.1f} {min_conv:<8.0f} {max_conv:<8.0f}")
    
    # # Box plot comparison
    # fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # # Final MSD box plot
    # msd_data = [10 * np.log10(np.array(final_msd_results[alg])) for alg in final_msd_results.keys()]
    # ax1.boxplot(msd_data, labels=list(final_msd_results.keys()))
    # ax1.set_ylabel('Final MSD (dB)')
    # ax1.set_title('Final MSD Distribution')
    # ax1.grid(True, alpha=0.3)
    
    # # Convergence time box plot
    # conv_data = [convergence_times[alg] for alg in convergence_times.keys()]
    # ax2.boxplot(conv_data, labels=list(convergence_times.keys()))
    # ax2.set_ylabel('Convergence Time (iterations)')
    # ax2.set_title('Convergence Time Distribution')
    # ax2.grid(True, alpha=0.3)
    
    # plt.tight_layout()
    # plt.show()
    
    return final_msd_results, convergence_times

if __name__ == "__main__":
    print("=== Probabilistic LMS Algorithm Simulation ===")
    print("Based on: 'A Probabilistic Least-Mean-Squares Filter' by Fernández-Bes et al.")
    print("With VSS-NLMS comparison included")
    print()
    
    # Run stationary experiment (Figure 1 reproduction)
    print("1. Stationary System Identification")
    msd_results = simulate_stationary_experiment(M=50, N=6000, num_runs=20)
    plot_stationary_results(msd_results)
    
    # Run tracking experiment
    print("\n2. Time-varying System Tracking")
    tracking_results, y_true, w_true = simulate_tracking_experiment(M=10, N=2000)
    plot_tracking_results(tracking_results, y_true)
    
    # Analyze algorithm properties
    print("\n3. Algorithm Properties Analysis")
    analyze_probabilistic_lms_properties()
    
    # Step size comparison analysis
    print("\n4. Step Size Adaptation Comparison")
    prob_lms, vss_nlms = analyze_step_size_comparison()
    
    # Detailed performance analysis
    print("\n5. Detailed Statistical Analysis")
    final_msd_results, convergence_times = detailed_performance_analysis()
    
    # Print comprehensive performance summary
    print("\n=== Comprehensive Performance Summary ===")
    final_msd_db = {}
    for alg_name, msd in msd_results.items():
        final_msd_db[alg_name] = 10 * np.log10(msd[-1000:].mean())
    
    print("Steady-state MSD (dB) - Stationary Experiment:")
    for alg_name, msd_db in final_msd_db.items():
        print("\n=== Comprehensive Performance Summary ===")
    final_msd_db = {}
    for alg_name, msd in msd_results.items():
        final_msd_db[alg_name] = 10 * np.log10(msd[-1000:].mean())
    
    print("Steady-state MSD (dB) - Stationary Experiment:")
    for alg_name, msd_db in final_msd_db.items():
        print(f"{alg_name:<10}: {msd_db:>8.2f} dB")
        
    print("\nKey Findings:")
    print("1. Probabilistic LMS shows robust performance in both stationary and non-stationary environments")
    print("2. The adaptive step size mechanism provides good balance between convergence speed and steady-state performance")
    print("3. The uncertainty tracking feature helps in detecting and adapting to system changes")
    
    print("\nSimulation Complete!")