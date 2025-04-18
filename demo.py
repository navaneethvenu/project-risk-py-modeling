import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog

from file_load import DEV_MODE, load_csv, load_default_files
from tornado_chart import tornado_chart

global baseline_data, risk_data


# Function to simulate a Beta Inverse transformation
# This function generates a random number from the Beta distribution
# using given alpha and beta parameters.
def beta_inv(p, alpha, beta):
    return np.random.beta(alpha, beta)

# Function to run the simulation
def run_simulation():
    global baseline_data, risk_data  # Access global variables
    
    # Check if both datasets are loaded
    if baseline_data is None or risk_data is None:
        print("Please upload both datasets.")
        return
    
    total_baseline_duration = baseline_data['originalDuration'].sum()  # Total project duration
    results = []  # List to store simulation results
    total_iterations = 1000  # Number of simulation runs
    
    # Iterate through each risk in the risk data
    for _, risk in risk_data.iterrows():

        print("risk:",risk['riskId'])

        # Ensure alpha and beta values are positive
        if risk['alpha'] <= 0 or risk['beta'] <= 0:
            continue
        
        if isinstance(risk['affectedActivity'], int):
            # It's a single integer, process it normally
            affected_activity_ids = [risk['affectedActivity']]
        elif isinstance(risk['affectedActivity'], str):
            # It's a string, check if it contains multiple values
            affected_activity_ids = risk['affectedActivity'].split(',')
        else:
            # Handle unexpected types (optional)
            affected_activity_ids = []

        for affected_activity_id in affected_activity_ids:
        
            print("activity:",affected_activity_id)
            # Find the affected activity in the baseline data
            affected_activity = baseline_data.loc[
                baseline_data['activityId'] == int(affected_activity_id)
            ]            
        
            # Skip if the affected activity is not found
            if affected_activity.empty:
                continue
        
            original_duration = affected_activity.iloc[0]['originalDuration']  # Get original duration
            print(original_duration)
            
            # Run Monte Carlo simulation
            for _ in range(total_iterations):
                rand_no = np.random.rand()  # Generate a random number between 0 and 1
                beta_value = beta_inv(rand_no, risk['alpha'], risk['beta'])  # Get Beta distributed value
                extra = risk['minimum'] + (risk['maximum'] - risk['minimum']) * beta_value  # Compute risk impact
                simulated_duration = original_duration + extra  # New simulated duration
                simulated_duration_divident = simulated_duration/original_duration
                total_simulated_duration = total_baseline_duration + extra  # Total project duration ~14
                
                # Store simulation result
                results.append({
                    "riskId": risk["riskId"],
                    "activityId": int(affected_activity_id),
                    "originalDuration": original_duration,
                    "simulatedDuration": simulated_duration,
                    "simulatedDurationDivident": simulated_duration_divident,
                    "totalSimulatedDuration": total_simulated_duration,
                })
    
    # Convert results list to DataFrame and save to CSV
    df_results = pd.DataFrame(results)
    df_results.to_csv("simulation_results.csv", index=False)
    print("Simulation complete. Results saved to simulation_results.csv")
    
    # Generate summary statistics for the simulation
    summary = df_results.groupby(["activityId", "riskId"]).agg(
        originalDuration=('originalDuration', 'first'),
        mean_simulated_divident=('simulatedDurationDivident', 'mean'),
        mean_simulated=('simulatedDuration', 'mean'),
        sd_simulated=('simulatedDuration', 'std'),
        var_simulated=('simulatedDuration', 'var'),
        mean_total_simulated=('totalSimulatedDuration', 'mean'),
        sd_total_simulated=('totalSimulatedDuration', 'std'),
        var_total_simulated=('totalSimulatedDuration', 'var')
    ).reset_index()
    
    df_summary = pd.DataFrame(summary)
    df_summary.to_csv("simulation_summary.csv", index=False)
    print("Summary statistics saved to simulation_summary.csv")
    
    aggregated = df_summary.groupby("activityId").agg(
        riskIds=('riskId', lambda x: ",".join(x.astype(str))),  # Concatenate riskIds
        originalDuration=('originalDuration', 'first')  # Keep the first occurrence
    ).reset_index()

    # Compute mean_simulated properly
    aggregated["mean_simulated"] = aggregated["originalDuration"] * df_summary.groupby("activityId").apply(
        lambda g: (g["mean_simulated"] / g["originalDuration"]).prod()
    ).values
    
    aggregated.to_csv("simulation_new_summary.csv", index=False)
    print("Updated Summary statistics saved to simulation_new_summary.csv")
    
    load_chart()
    
    
def load_chart():
    print("loading chart")
    # data for chart
    labels = np.char.array([
        "Variable 1\n 2.0 - 5.0",
        "Variable 2\n 11% - 15%",
        "Variable 3\n $200 - $300",
        "Variable 4\n $12 - $14",
        "Variable 5\n Off - On",
        "Variable 6\n Low - High",
    ])

    midpoint = 20

    # data values
    low_values = np.array([ # value order corresponds to label order
        19.5,
        18,
        15.5,
        12,
        32.5,
        4 
    ])

    high_values = np.array([
        20.5,
        22,
        24.5,
        28,
        7.5,
        36
    ])

    var_effect = np.abs(high_values - low_values)/midpoint

    data = pd.DataFrame({'Labels': labels,
                        'Low values': low_values,
                        'High values': high_values,
                        'Variable effect' : var_effect
                        })

    # sorts effect high to low (adjust to preference)
    data = data.sort_values(
        'Variable effect',
        ascending=True,
        inplace=False,
        ignore_index=False,
        key=None
    )
    
    tornado_chart(data,labels, midpoint, data['Low values'], data['High values'])
        


# Initialize global variables
baseline_data, risk_data = None, None

# Setup Tkinter UI
root = tk.Tk()
root.title("Risk Simulation")

# Create a frame for layout
frame = tk.Frame(root)
frame.pack(pady=20)

# Button to load baseline data
btn_load_baseline = tk.Button(frame, text="Load Baseline Data", 
                              command=lambda: globals().update(baseline_data=load_csv(lbl_baseline,pd, filedialog)))

# Button to load risk data
btn_load_risk = tk.Button(frame, text="Load Risk Data", 
                          command=lambda: globals().update(risk_data=load_csv(lbl_risk,pd, filedialog)))

# Button to run the simulation
btn_run = tk.Button(root, text="Run Simulation", command=run_simulation)

# Labels to display loaded file names
lbl_baseline = tk.Label(frame, text="No file loaded", fg="grey")
lbl_risk = tk.Label(frame, text="No file loaded", fg="grey")

# Arrange buttons and labels using grid layout
btn_load_baseline.grid(row=0, column=0, padx=10)
lbl_baseline.grid(row=1, column=0)
btn_load_risk.grid(row=2, column=0, padx=10)
lbl_risk.grid(row=3, column=0)

# Place run simulation button
btn_run.pack(pady=20)

# Automatically load default files in development mode
if DEV_MODE:
    resultFiles=load_default_files(lbl_baseline,lbl_risk, pd, filedialog)
    baseline_data = resultFiles["baseline"]
    risk_data = resultFiles["risk"]
    run_simulation()

# Start Tkinter event loop
root.mainloop()
