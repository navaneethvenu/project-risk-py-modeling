# Enable development mode
DEV_MODE = True  # Set to False when deploying


# Default file paths (update these with your actual file locations)
DEFAULT_BASELINE_FILE = "/Users/navaneethvenu/Downloads/Dad Project Risk - Activities.csv"
DEFAULT_RISK_FILE = "/Users/navaneethvenu/Downloads/Dad Project Risk - Risk.csv"

# Function to load CSV data
# This function opens a file dialog to select a CSV file
# and loads it into a pandas DataFrame.
def load_csv(label, pd, filedialog, default_file=None,):
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
def load_default_files(lbl_baseline,lbl_risk, pd, filedialog):
    """Loads default CSV files if running in development mode."""
    global baseline_data, risk_data
    baseline_data = load_csv(lbl_baseline, pd, filedialog, DEFAULT_BASELINE_FILE)
    risk_data = load_csv(lbl_risk, pd, filedialog, DEFAULT_RISK_FILE)
