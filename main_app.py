import streamlit as st
import pandas as pd
import os
from difflib import get_close_matches
from BRE import calculate_platform_thickness

# Check if openpyxl is installed
try:
    import openpyxl
except ImportError:
    st.error("The 'openpyxl' library is required to read Excel files. Please install it by running: `pip install openpyxl`")
    st.stop()  # Stop the app if openpyxl is not installed

# Function to select soil type
def get_soil_type():
    st.write("Select soil type:")
    soil_type = st.radio("Soil Type", ["Clay", "Granular"])
    return soil_type.lower()

# Function to get clay soil parameters
def get_clay_soil_parameters():
    platform_phi_k = st.text_input("Enter platform_phi_k (or press Enter to use default range [40, 45, 50, 55]):").strip()
    subgrade_cu_k_values = st.text_input("Enter subgrade_cu_k_values (or press Enter to use default range [20, 30, 40, 50, 60]):").strip()
    
    if not platform_phi_k:
        platform_phi_k = [40, 45, 50, 55]
    else:
        platform_phi_k = [int(platform_phi_k)]
    
    if not subgrade_cu_k_values:
        subgrade_cu_k_values = list(range(20, 61, 10))
    else:
        subgrade_cu_k_values = [int(subgrade_cu_k_values)]
    
    return platform_phi_k, subgrade_cu_k_values

# Function to select machine from Excel
def select_machine_from_excel(file_path, sheet_name, method):
    if not os.path.exists(file_path):
        st.error(f"File not found at: {file_path}")
        return None, None
    
    # Load the Excel file
    data_sheet = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Define column indices based on the selected method
    if method == "EN16228":
        col_b = 12  # Column M (Index 12)
        col_qu = 21  # Column V (Index 21)
        col_L1 = 25  # Column Z (Index 25)
    elif method == "EN16228 Simplified":
        col_b = 12  # Column M (Index 12)
        col_qu = 23  # Column W (Index 23)
        col_L1 = 27  # Column AA (Index 27)
    elif method == "FPS":
        col_b = 12  # Column M (Index 12)
        col_qu = 30  # Column AD (Index 30)
        col_L1 = 34  # Column AH (Index 34)
    elif method == "Austrian":
        col_b = 12  # Column M (Index 12)
        col_qu = 36  # Column AJ (Index 36)
        col_L1 = 37  # Column AK (Index 37)
    
    # Extract relevant columns
    relevant_data = data_sheet.iloc[:, [1, 2, col_b, col_qu, col_L1]].copy()  # Columns: Machine Name, MODE, b, qu, L1
    relevant_data.columns = ['Machine', 'MODE', 'b', 'qu', 'L1']
    
    # Convert columns to numeric, coerce errors to NaN
    relevant_data['b'] = pd.to_numeric(relevant_data['b'], errors='coerce')
    relevant_data['qu'] = pd.to_numeric(relevant_data['qu'], errors='coerce')
    relevant_data['L1'] = pd.to_numeric(relevant_data['L1'], errors='coerce')
    
    # Filter data
    filtered_data = relevant_data[
        (relevant_data['b'] >= 0) &
        (relevant_data['qu'] >= 110) &
        (relevant_data['L1'] >= 0) &
        (relevant_data['L1'] <= 10000)
    ].copy()
    
    # Drop rows with NaN values
    filtered_data = filtered_data.dropna()
    
    # Ask the user to enter the machine name
    machine_names = filtered_data['Machine'].dropna().unique().tolist()
    user_input = st.text_input("Enter machine name (or part of the name):").strip()
    
    if user_input:  # Only proceed if the user has entered something
        matches = get_close_matches(user_input, machine_names, n=5, cutoff=0.3)
        
        if matches:
            selected_machine = st.selectbox("Select the correct machine:", matches)
            return selected_machine, filtered_data[filtered_data['Machine'] == selected_machine]
        else:
            st.error("No matches found. Please try again.")
            return None, None
    else:
        return None, None  # Return None if no input is provided

# Function to get manual input
def get_manual_input():
    machine_weight = st.number_input("Enter machine weight (kg):", min_value=0.0)
    b = st.number_input("Enter b (mm):", min_value=0.0)
    qu = st.number_input("Enter qu (kPa):", min_value=0.0)
    L1 = st.number_input("Enter L1 (mm):", min_value=0.0)
    
    return {
        "machine_weight": machine_weight,
        "b": b,
        "qu": qu,
        "L1": L1
    }

# Main function
def main():
    st.title("Platform Thickness Calculator")
    
    # Select scenario
    scenario_choice = st.radio("Select scenario:", ["Machine Selection from Excel", "Manual Input"])
    
    # Select soil type
    soil_type = get_soil_type()
    if soil_type == "clay":
        platform_phi_k, subgrade_cu_k_values = get_clay_soil_parameters()
    elif soil_type == "granular":
        st.warning("Currently not accepting granular soil requests.")
        return
    
    # Select method
    method = st.selectbox("Select method:", ["EN16228", "EN16228 Simplified", "FPS", "Austrian"])
    
    if scenario_choice == "Machine Selection from Excel":
        # Scenario 1: Machine Selection from Excel
        file_path = "Bearing Pressure rev30.xlsx"  # Use relative path
        sheet_name = "Data"
        selected_machine, machine_data = select_machine_from_excel(file_path, sheet_name, method)
        
        if selected_machine is not None:
            st.write(f"Selected machine: {selected_machine}")
            
            # Perform calculations for each mode
            for index, row in machine_data.iterrows():
                mode = row["MODE"]
                b = row["b"] / 1000  # Convert mm to meters
                qu = row["qu"]
                L1 = row["L1"] / 1000  # Convert mm to meters
                
                # Prepare configuration
                cfg = {
                    "b": b,
                    "qu": qu,
                    "L1": L1,
                    "platform_phi_k": platform_phi_k[0],
                    "platform_gamma_k": 20,
                    "gamma_BRECaseNoPlatform": 1.5,
                    "gamma_BRECasePlatform": 1.2
                }
                
                # Calculate platform thickness
                thicknesses = calculate_platform_thickness(cfg, subgrade_cu_k_values)
                for thickness, comment in thicknesses:
                    # Round off the thickness to 2 decimal places
                    thickness_rounded = round(thickness, 2)
                    # Display the result with units and comment
                    st.write(f"Machine: {selected_machine}, Mode: {mode}")
                    st.write(f"Platform Thickness: {thickness_rounded} m")
                    st.write(f"Comment: {comment}")
    
    elif scenario_choice == "Manual Input":
        # Scenario 2: Manual Input
        inputs = get_manual_input()
        
        # Prepare configuration
        cfg = {
            "b": inputs["b"] / 1000,  # Convert mm to meters
            "qu": inputs["qu"],
            "L1": inputs["L1"] / 1000,  # Convert mm to meters
            "platform_phi_k": platform_phi_k[0],
            "platform_gamma_k": 20,
            "gamma_BRECaseNoPlatform": 1.5,
            "gamma_BRECasePlatform": 1.2
        }
        
        # Calculate platform thickness
        thicknesses = calculate_platform_thickness(cfg, subgrade_cu_k_values)
        for thickness, comment in thicknesses:
            # Round off the thickness to 2 decimal places
            thickness_rounded = round(thickness, 2)
            # Display the result with units and comment
            st.write(f"Platform Thickness: {thickness_rounded} m")
            st.write(f"Comment: {comment}")

# Run the main function
if __name__ == "__main__":
    main()
