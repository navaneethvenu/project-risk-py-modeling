import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from itertools import permutations
from collections import defaultdict


# Enable development mode
DEV_MODE = True  # Set to False when deploying


# Default file paths (update these with your actual file locations)
DEFAULT_BASELINE_FILE = "/Users/navaneethvenu/Downloads/Dad Project Risk - Activities.csv"
DEFAULT_RISK_FILE = "/Users/navaneethvenu/Downloads/Dad Project Risk - Risk.csv"

# Function to load CSV data
# This function opens a file dialog to select a CSV file
# and loads it into a pandas DataFrame.
def load_csv(label, default_file=None):
    """Opens a file dialog to select a CSV file or loads a default file in development mode."""
    if DEV_MODE and default_file:  # Load default file in dev mode
        label.config(text=f"Loaded (Default): {default_file.split('/')[-1]}")
        return pd.read_csv(default_file)
    
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        label.config(text=f"Loaded: {file_path.split('/')[-1]}")  # Update label text
        return pd.read_csv(file_path)  # Read CSV file into DataFrame
    return None  # Return None if no file is selected


# Function to load default files for development mode
def load_default_files():
    """Loads default CSV files if running in development mode."""
    global baseline_data, risk_data
    baseline_data = load_csv(lbl_baseline, DEFAULT_BASELINE_FILE)
    risk_data = load_csv(lbl_risk, DEFAULT_RISK_FILE)

# Function to simulate a Beta Inverse transformation
# This function generates a random number from the Beta distribution
# using given alpha and beta parameters.
def beta_inv(p, alpha, beta):
    return np.random.beta(alpha, beta)

def risk_combinations(risk_data):
    # Extract the 'id' column as a list
    ids = risk_data['riskId'].tolist()

    seen = set()
    raw_combinations = []

    for start_index, anchor in enumerate(ids):
        rest = ids[:start_index] + ids[start_index + 1:]

        for r in range(0, len(rest) + 1):
            for perm in permutations(rest, r):
                combo = (anchor,) + perm
                key = frozenset(combo)
                if key not in seen:
                    seen.add(key)
                    raw_combinations.append((start_index, combo))

    # Now sort by:
    # 1. anchor index (to keep R1, R2, R3... order)
    # 2. combo length (shorter combos first)
    # 3. actual tuple (to break ties lexicographically)
    sorted_combinations = sorted(
        raw_combinations,
        key=lambda x: (x[0], len(x[1]), x[1])
    )
        
    print("booooo")
    return sorted_combinations;

def group_risks(risk_data):
    # Build risk appearance order
    risk_order = {risk_id: idx for idx, risk_id in enumerate(risk_data['riskId'])}

    # Group activities to risk IDs
    activity_to_risks = defaultdict(list)

    for _, row in risk_data.iterrows():
        for act in row['affectedActivity'].split(','):
            act = act.strip()
            if act and row['riskId'] not in activity_to_risks[act]:
                activity_to_risks[act].append(row['riskId'])

    # Group by risk combinations (as tuples) → list of activities
    risks_to_activities = defaultdict(list)
    for activity, risks in activity_to_risks.items():
        key = tuple(risks)  # preserve order
        risks_to_activities[key].append(activity)

    # Sort by lexicographical risk appearance order
    sorted_groups = sorted(
        risks_to_activities.items(),
        key=lambda x: [risk_order[r] for r in x[0]]
    )

    # Format result: list of tuples (activity_group_str, risks)
    result = []
    for risks, activities in sorted_groups:
        act_group = ','.join(sorted(activities, key=int))
        result.append((act_group, list(risks)))

    return result


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
    
    risk_combos = risk_combinations(risk_data=risk_data)
    
    # Print only the combos
    for _, combo in risk_combos:
        print(combo)
        
        
    print("\n\n\nactivitymapping\n")
        
    risk_groups =  group_risks(risk_data=risk_data)
    
    print(risk_groups)
    
    for activities, risks in risk_groups:
        print(risks,"\n")
        
        # Run Monte Carlo simulation
        for _ in range(total_iterations):
            rand_no = np.random.rand()  # Generate a random number between 0 and 1
            for activity in activities.split(","):
                print(activity)
                print("activity:",activity)
                # Find the affected activity in the baseline data
                affected_activity = baseline_data.loc[
                    baseline_data['activityId'] == int(activity)
                ]            
            
                # Skip if the affected activity is not found
                if affected_activity.empty:
                    continue
            
                original_duration = affected_activity.iloc[0]['originalDuration']  # Get original duration
                print("OG Duration: ",original_duration,"\n")
                
        

    
    
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
                              command=lambda: globals().update(baseline_data=load_csv(lbl_baseline)))

# Button to load risk data
btn_load_risk = tk.Button(frame, text="Load Risk Data", 
                          command=lambda: globals().update(risk_data=load_csv(lbl_risk)))

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
    load_default_files()
    run_simulation()

# Start Tkinter event loop
root.mainloop()