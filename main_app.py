import streamlit as st
import pandas as pd
import numpy as np
import os
from difflib import get_close_matches
from BRE import compute_thicknesses_unbewehrt

# Check if openpyxl is installed
try:
    import openpyxl
except ImportError:
    st.error("The 'openpyxl' library is required to read Excel files. Please install it by running: `pip install openpyxl`")
    st.stop()  # Stop the app if openpyxl is not installed

# Function to fetch soil details
def get_soil_details():
    st.write("Select soil property ranges:")
    range_choice = st.radio("Range Choice", ["Default Ranges", "Custom Ranges"])

    if range_choice == "Default Ranges":
        platform_phi_k = [40, 45, 50]
        subgrade_cu_k = [20, 30, 40]
    else:
        st.write("Enter custom ranges for platform_phi_k and subgrade_cu_k:")
        platform_phi_k_min = st.number_input("Min platform_phi_k (degrees):", min_value=0.0)
        platform_phi_k_max = st.number_input("Max platform_phi_k (degrees):", min_value=platform_phi_k_min)
        platform_phi_k_step = st.number_input("Step for platform_phi_k (degrees):", min_value=1.0)
        subgrade_cu_k_min = st.number_input("Min subgrade_cu_k (kPa):", min_value=0.0)
        subgrade_cu_k_max = st.number_input("Max subgrade_cu_k (kPa):", min_value=subgrade_cu_k_min)
        subgrade_cu_k_step = st.number_input("Step for subgrade_cu_k (kPa):", min_value=1.0)

        platform_phi_k = list(np.arange(platform_phi_k_min, platform_phi_k_max + 1, platform_phi_k_step))
        subgrade_cu_k = list(np.arange(subgrade_cu_k_min, subgrade_cu_k_max + 1, subgrade_cu_k_step))

    return platform_phi_k, subgrade_cu_k

# Function to select machine and modes from Excel
def select_machine_from_excel(file_path, sheet_name):
    if not os.path.exists(file_path):
        st.error(f"File not found at: {file_path}")
        return None, None

    data_sheet = pd.read_excel(file_path, sheet_name=sheet_name)

    # Extract machine names
    machine_names = data_sheet.iloc[:, 1].dropna().unique().tolist()

    # Ask the user to input a machine name
    user_input = st.text_input("Enter machine name (or part of the name):").strip()

    if user_input:
        matches = get_close_matches(user_input, machine_names, n=5, cutoff=0.3)
        if matches:
            selected_machine = st.selectbox("Select the correct machine:", matches)
            relevant_data = data_sheet[data_sheet.iloc[:, 1] == selected_machine]
            return selected_machine, relevant_data
        else:
            st.error("No matches found. Please try again.")
    return None, None

# Main function
def main():
    st.title("Platform Thickness Calculator")

    # Select scenario
    scenario_choice = st.radio("Select scenario:", ["Expert Mode", "Guided Mode"])

    if scenario_choice == "Expert Mode":
        # Expert Mode: Single values
        L1 = st.number_input("Enter L1 (mm):", min_value=0.0) / 1000  # Convert to meters
        b = st.number_input("Enter b (mm):", min_value=0.0) / 1000  # Convert to meters
        qu = st.number_input("Enter qu (kPa):", min_value=0.0)
        platform_phi_k = [st.number_input("Enter platform_phi_k (degrees):", min_value=0.0)]
        subgrade_cu_k = [st.number_input("Enter subgrade_cu_k (kPa):", min_value=0.0)]

        cfg = {
            "L1": L1,
            "b": b,
            "qu": qu,
            "platform_phi_k": platform_phi_k,
            "platform_gamma_k": 20,
            "gamma_BRECaseNoPlatform": 1.5,
            "gamma_BRECasePlatform": 1.2
        }

        results = []
        for platform_phi_k_value in platform_phi_k:
            for subgrade_cu_k_value in subgrade_cu_k:
                cfg['platform_phi_k'] = platform_phi_k_value
                thickness, comment = compute_thicknesses_unbewehrt(subgrade_cu_k_value, cfg)
                results.append({
                    "platform_phi_k": platform_phi_k_value,
                    "subgrade_cu_k": subgrade_cu_k_value,
                    "Thickness (m)": round(thickness, 2),
                    "Comment": comment
                })

        st.dataframe(pd.DataFrame(results))

    elif scenario_choice == "Guided Mode":
        file_path = "Bearing Pressure rev30.xlsx"
        sheet_name = "Data"

        selected_machine, machine_data = select_machine_from_excel(file_path, sheet_name)
        if selected_machine:
            platform_phi_k, subgrade_cu_k = get_soil_details()

            if platform_phi_k and subgrade_cu_k:
                results = []
                for _, row in machine_data.iterrows():
                    mode = row["MODE"]
                    b = row["b"] / 1000  # Convert mm to meters
                    qu = row["qu"]
                    L1 = row["L1"] / 1000  # Convert mm to meters

                    cfg = {
                        "b": b,
                        "qu": qu,
                        "L1": L1,
                        "platform_phi_k": [],  # Filled in loop
                        "platform_gamma_k": 20,
                        "gamma_BRECaseNoPlatform": 1.5,
                        "gamma_BRECasePlatform": 1.2
                    }

                    for phi in platform_phi_k:
                        for cu in subgrade_cu_k:
                            cfg['platform_phi_k'] = phi
                            thickness, comment = compute_thicknesses_unbewehrt(cu, cfg)
                            results.append({
                                "Machine": selected_machine,
                                "Mode": mode,
                                "platform_phi_k": phi,
                                "subgrade_cu_k": cu,
                                "Thickness (m)": round(thickness, 2),
                                "Comment": comment
                            })

                st.dataframe(pd.DataFrame(results))

if __name__ == "__main__":
    main()
