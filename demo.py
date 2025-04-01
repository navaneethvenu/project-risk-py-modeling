import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog

# Function to load CSV data
def load_csv(label):
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        label.config(text=f"Loaded: {file_path.split('/')[-1]}")
        return pd.read_csv(file_path)
    return None

# Beta Inverse Simulation
def beta_inv(p, alpha, beta):
    return np.random.beta(alpha, beta)

# Run simulation
def run_simulation():
    global baseline_data, risk_data
    
    if baseline_data is None or risk_data is None:
        print("Please upload both datasets.")
        return
    
    total_baseline_duration = baseline_data['originalDuration'].sum()
    results = []
    total_iterations = 1000
    
    for _, risk in risk_data.iterrows():
        if risk['alpha'] <= 0 or risk['beta'] <= 0:
            continue
        
        affected_activity = baseline_data.loc[
            baseline_data['activityId'] == risk['affectedActivity']
        ]
        
        if affected_activity.empty:
            continue
        
        original_duration = affected_activity.iloc[0]['originalDuration']
        
        for _ in range(total_iterations):
            rand_no = np.random.rand()
            beta_value = beta_inv(rand_no, risk['alpha'], risk['beta'])
            extra = risk['minimum'] + (risk['maximum'] - risk['minimum']) * beta_value
            simulated_duration = original_duration + extra
            total_simulated_duration = total_baseline_duration + extra
            
            results.append({
                "activityId": risk['affectedActivity'],
                "originalDuration": original_duration,
                "simulatedDuration": simulated_duration,
                "totalSimulatedDuration": total_simulated_duration,
            })
    
    df_results = pd.DataFrame(results)
    df_results.to_csv("simulation_results.csv", index=False)
    print("Simulation complete. Results saved to simulation_results.csv")
    
    # Generate summary statistics
    summary = df_results.groupby("activityId").agg(
        originalDuration=('originalDuration', 'first'),
        mean_simulated=('simulatedDuration', 'mean'),
        sd_simulated=('simulatedDuration', 'std'),
        var_simulated=('simulatedDuration', 'var'),
        mean_total_simulated=('totalSimulatedDuration', 'mean'),
        sd_total_simulated=('totalSimulatedDuration', 'std'),
        var_total_simulated=('totalSimulatedDuration', 'var')
    ).reset_index()
    
    summary.to_csv("simulation_summary.csv", index=False)
    print("Summary statistics saved to simulation_summary.csv")

# UI setup
baseline_data, risk_data = None, None
root = tk.Tk()
root.title("Risk Simulation")

frame = tk.Frame(root)
frame.pack(pady=20)

btn_load_baseline = tk.Button(frame, text="Load Baseline Data", 
                              command=lambda: globals().update(baseline_data=load_csv(lbl_baseline)))
btn_load_risk = tk.Button(frame, text="Load Risk Data", 
                          command=lambda: globals().update(risk_data=load_csv(lbl_risk)))
btn_run = tk.Button(root, text="Run Simulation", command=run_simulation)

lbl_baseline = tk.Label(frame, text="No file loaded", fg="grey")
lbl_risk = tk.Label(frame, text="No file loaded", fg="grey")

btn_load_baseline.grid(row=0, column=0, padx=10)
lbl_baseline.grid(row=1, column=0)
btn_load_risk.grid(row=2, column=0, padx=10)
lbl_risk.grid(row=3, column=0)

btn_run.pack(pady=20)

root.mainloop()