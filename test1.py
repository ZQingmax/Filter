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
        self.sigma_k_squared = sigma_d_squared  # Uncertainty estimate
        
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
        
        # RLS update
        k = self.P @ x_k / (self.lam + x_k.T @ self.P @ x_k)
        self.w = self.w + k * error
        self.P = (self.P - np.outer(k, x_k.T @ self.P)) / self.lam
        
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
    algorithms = ['LMS', 'NLMS', 'RLS', 'ProbLMS1', 'ProbLMS2']
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
            'RLS': RLS(M, forgetting_factor=1.0, epsilon=0.01),
            'ProbLMS1': ProbabilisticLMS(M, sigma_n_squared),  # Perfect knowledge
            'ProbLMS2': ProbabilisticLMS(M, sigma_n_squared/100)  # Suboptimal
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
    """Plot results for stationary experiment"""
    plt.figure(figsize=(12, 8))
    
    colors = ['blue', 'green', 'red', 'orange', 'purple']
    linestyles = ['-', '--', '-.', '-', ':']
    
    for i, (alg_name, msd) in enumerate(msd_results.items()):
        msd_db = 10 * np.log10(msd + 1e-15)  # Convert to dB, avoid log(0)
        plt.plot(msd_db, label=alg_name, color=colors[i], 
                linestyle=linestyles[i], linewidth=2)
    
    plt.xlabel('Iterations')
    plt.ylabel('MSD (dB)')
    plt.title('Performance Comparison: Stationary Environment')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ylim([-60, -20])
    plt.xlim([0, 6000])
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

if __name__ == "__main__":
    print("=== Probabilistic LMS Algorithm Simulation ===")
    print("Based on: 'A Probabilistic Least-Mean-Squares Filter' by Fernández-Bes et al.")
    print()
    
    # Run stationary experiment (Figure 1 reproduction)
    print("1. Stationary System Identification")
    msd_results = simulate_stationary_experiment(M=50, N=6000, num_runs=20)  # Reduced runs for speed
    plot_stationary_results(msd_results)
    
    # Run tracking experiment
    print("\n2. Time-varying System Tracking")
    tracking_results, y_true, w_true = simulate_tracking_experiment(M=10, N=2000)
    plot_tracking_results(tracking_results, y_true)
    
    # Analyze algorithm properties
    print("\n3. Algorithm Properties Analysis")
    analyze_probabilistic_lms_properties()
    
    # Print final performance summary
    print("\n=== Performance Summary ===")
    final_msd_db = {}
    for alg_name, msd in msd_results.items():
        final_msd_db[alg_name] = 10 * np.log10(msd[-1000:].mean())  # Average last 1000 samples
    
    print("Steady-state MSD (dB):")
    for alg_name, msd_db in final_msd_db.items():
        print(f"{alg_name:>10}: {msd_db:>8.2f}")
    
    print("\nKey advantages of Probabilistic LMS:")
    print("1. Adaptive step-size without manual tuning")
    print("2. Uncertainty quantification")
    print("3. Linear computational complexity O(M)")
    print("4. Fewer parameters than other variable step-size LMS")
    print("5. Clear physical interpretation of parameters")