import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
from pulp import *

from file_load import DEV_MODE, load_csv, load_default_files
from tornado_chart import tornado_chart_centered
from globals import original_set_duration, total_contigency_cost

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

    total_baseline_duration = baseline_data[
        "originalDuration"
    ].sum()  # Total project duration
    results = []  # List to store simulation results
    total_iterations = 2000  # Number of simulation runs
    individual_risks = []

    # Iterate through each risk in the risk data
    for _, risk in risk_data.iterrows():

        print("risk:", risk["riskId"])

        # Ensure alpha and beta values are positive
        if risk["alpha"] <= 0 or risk["beta"] <= 0:
            continue

        if isinstance(risk["affectedActivity"], float):
            # It's a single integer, process it normally
            affected_activity_ids = [risk["affectedActivity"]]
        elif isinstance(risk["affectedActivity"], str):
            # It's a string, check if it contains multiple values
            affected_activity_ids = risk["affectedActivity"].split(",")
        else:
            # Handle unexpected types (optional)
            affected_activity_ids = []

        for affected_activity_id in affected_activity_ids:

            print("activity:", affected_activity_id)

            # Find the affected activity in the baseline data
            affected_activity = baseline_data.loc[
                (baseline_data["activityId"]) == float(affected_activity_id)
            ]

            # Skip if the affected activity is not found
            if affected_activity.empty:
                continue

            original_duration = affected_activity.iloc[0][
                "originalDuration"
            ]  # Get original duration
            print(original_duration)

            avgTimeImpact = round(
                risk["probability"] * risk["timeImpact"] * original_duration
            )

            individual_risks.append(
                {
                    "riskId": risk["riskId"],
                    "title": risk["title"],
                    "affectedActivity": (affected_activity_id),
                    "probability": risk["probability"],
                    "timeImpact": risk["timeImpact"],
                    "originalDuration": original_duration,
                    "avgTimeImpact": avgTimeImpact,
                    "o": round(0.9 * avgTimeImpact),
                    "m": avgTimeImpact,
                    "p": round(1.5 * avgTimeImpact),
                    "avg": round((3.4 * avgTimeImpact) / 3),
                    "alpha": risk["alpha"],
                    "beta": risk["beta"],
                    "riskMitigationCost": risk["riskMitigationCost"],
                    "contigencyCost": risk["contigencyCost"],
                }
            )

    # Convert seperated risks to DataFrame and save to CSV
    df_separate_risk = pd.DataFrame(individual_risks)
    df_separate_risk.to_csv("individual_risks.csv", index=False)
    print("Simulation complete. Individual Risks saved to individual_risks.csv")

    df_grouped_risk = (
        df_separate_risk[
            [
                "riskId",
                "affectedActivity",
                "o",
                "p",
                "alpha",
                "beta",
                "riskMitigationCost",
                "contigencyCost",
            ]
        ]
        .groupby("riskId")
        .agg(
            {
                "affectedActivity": lambda x: ",".join(map(str, x)),
                "o": "min",
                "p": "max",
                "alpha": "first",
                "beta": "first",
                "riskMitigationCost": "first",
                "contigencyCost": "first",
            }
        )
        .reset_index()
    )

    df_grouped_risk.rename(columns={"o": "minimum", "p": "maximum"}, inplace=True)

    # Convert seperated risks to DataFrame and save to CSV
    df_grouped_risk.to_csv("grouped_risks.csv", index=False)
    print("Simulation complete. Grouped Risks saved to grouped_risks.csv")

    for _, grisk in df_grouped_risk.iterrows():

        print("monte carlo on ", grisk["riskId"])

        # Run Monte Carlo simulation
        for _ in range(total_iterations):
            rand_no = np.random.rand()  # Generate a random number between 0 and 1
            beta_value = beta_inv(
                rand_no, grisk["alpha"], grisk["beta"]
            )  # Get Beta distributed value
            extra = (
                grisk["minimum"] + (grisk["maximum"] - grisk["minimum"]) * beta_value
            )  # Compute risk impact
            simulated_duration = original_duration + extra  # New simulated duration
            simulated_duration_divident = simulated_duration / original_duration
            total_simulated_duration = (
                original_set_duration + extra
            )  # Total project duration ~14

            # Store simulation result
            results.append(
                {
                    "riskId": grisk["riskId"],
                    "activityId": grisk["affectedActivity"],
                    "simulatedDuration": simulated_duration,
                    "totalSimulatedDuration": total_simulated_duration,
                    "riskMitigationCost": grisk["riskMitigationCost"],
                    "contigencyCost": grisk["contigencyCost"],
                }
            )

    # Convert results list to DataFrame and save to CSV
    df_results = pd.DataFrame(results)
    df_results.to_csv("simulation_results.csv", index=False)
    print("Simulation complete. Results saved to simulation_results.csv")

    # Generate summary statistics for the simulation
    summary = (
        df_results.groupby("riskId")
        .agg(
            affected_activity=("activityId", "first"),
            mean_simulated=("simulatedDuration", "mean"),
            sd_simulated=("simulatedDuration", "std"),
            var_simulated=("simulatedDuration", "var"),
            mean_total_simulated=("totalSimulatedDuration", "mean"),
            sd_total_simulated=("totalSimulatedDuration", "std"),
            var_total_simulated=("totalSimulatedDuration", "var"),
            riskMitigationCost=("riskMitigationCost", "first"),
            contigencyCost=("contigencyCost", "first"),
        )
        .reset_index()
    )

    summary["impact"] = summary["mean_total_simulated"] - original_set_duration

    summary = summary.sort_values("impact", ascending=False).reset_index(drop=True)

    df_summary = pd.DataFrame(summary)
    df_summary.to_csv("simulation_summary.csv", index=False)
    print("Summary statistics saved to simulation_summary.csv")

    # linear programming

    print("starting lp")

    # input data

    objective_coeffs = {
        row["riskId"]: (row["riskMitigationCost"]) for _, row in summary.iterrows()
    }

    print(objective_coeffs)

    constraints = [
        # base constraint: risk variable ≤ impact
        *[
            {"vars": {row["riskId"]: 1}, "sense": "<=", "rhs": round(row["impact"])}
            for _, row in summary.iterrows()
        ],
        # impact * variable ≤ cost
        *[
            {
                "vars": {row["riskId"]: row["riskMitigationCost"]},
                "sense": "<=",
                "rhs": row["contigencyCost"],
            }
            for _, row in summary.iterrows()
        ],
        # 3. Sum of (risk * impact) ≤ overall_cost
        {
            "vars": {
                row["riskId"]: row["riskMitigationCost"]
                for _, row in summary.iterrows()
            },
            "sense": "<=",
            "rhs": total_contigency_cost,
        },
    ]

    print(constraints)

    # Step 1: Create the model

    model = LpProblem("dynamic_lp", LpMaximize)

    # Step 2: Dynamically create variables
    variables = {
        name: LpVariable(name, lowBound=0, cat="Continuous")
        for name in objective_coeffs
    }

    # Step 3: Set the objective
    model += lpSum(coeff * variables[var] for var, coeff in objective_coeffs.items())

    # Step 4: Add constraints
    for constraint in constraints:
        expr = lpSum(
            coeff * variables[var] for var, coeff in constraint["vars"].items()
        )
        if constraint["sense"] == "<=":
            model += expr <= constraint["rhs"]
        elif constraint["sense"] == ">=":
            model += expr >= constraint["rhs"]
        elif constraint["sense"] == "==":
            model += expr == constraint["rhs"]

    # Step 5: Solve
    solver = getSolver("PULP_CBC_CMD")
    status = model.solve(solver=solver)

    # Step 6: Output results
    if LpStatus[status] == "Optimal":
        print("Optimal solution found.")
        print(f"Objective value: z* = {value(model.objective)}")
        for name, var in variables.items():
            print(f"{name}* = {value(var)}")
    else:
        print("No optimal solution found.")

        model = pulp.LpProblem("linear_programming", LpMinimize)
        # get solver
        solver = getSolver("PULP_CBC_CMD")

    # Step 7: Plot results
    selected = {
        var_name: value(var)
        for var_name, var in variables.items()
        if value(var) > 0  # only plot selected risks
    }

    plt.figure(figsize=(8, 4))
    plt.bar(selected.keys(), selected.values(), color="skyblue")
    plt.title("Selected Risk Allocations")
    plt.xlabel("Risk ID")
    plt.ylabel("Selected Value")
    plt.grid(True, axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()

    load_chart(summary)
    plt.show()


def load_chart(summary):
    print("loading chart")

    labels = []

    # data for chart
    for i in range(len(summary)):
        labels.append(summary.loc[i, "riskId"])

    values = []

    # data values
    for i in range(len(summary)):
        values.append(summary.loc[i, "impact"])

    values = np.array(values)

    data = pd.DataFrame(
        {
            "Labels": labels,
            "values": values,
        }
    )

    tornado_chart_centered(labels, values, title="Risk Prioritisation")


# Initialize global variables
baseline_data, risk_data = None, None

# Setup Tkinter UI
root = tk.Tk()
root.title("Risk Simulation")

# Create a frame for layout
frame = tk.Frame(root)
frame.pack(pady=20)

# Button to load baseline data
btn_load_baseline = tk.Button(
    frame,
    text="Load Baseline Data",
    command=lambda: globals().update(
        baseline_data=load_csv(lbl_baseline, pd, filedialog)
    ),
)

# Button to load risk data
btn_load_risk = tk.Button(
    frame,
    text="Load Risk Data",
    command=lambda: globals().update(risk_data=load_csv(lbl_risk, pd, filedialog)),
)

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
    resultFiles = load_default_files(lbl_baseline, lbl_risk, pd, filedialog)
    baseline_data = resultFiles["baseline"]
    risk_data = resultFiles["risk"]
    run_simulation()

# Start Tkinter event loop
root.mainloop()
