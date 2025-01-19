import streamlit as st
import pandas as pd
import os
from difflib import get_close_matches
from BRE import calculate_platform_thickness

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
def select_machine_from_excel(file_path, sheet_name):
    if not os.path.exists(file_path):
        st.error(f"File not found at: {file_path}")
        return None, None
    
    # Load the Excel file
    data_sheet = pd.read_excel(file_path, sheet_name=sheet_name)
    machine_names = data_sheet.iloc[:, 0].dropna().unique().tolist()  # Assuming machine names are in the first column
    
    # Ask the user to enter the machine name
    user_input = st.text_input("Enter machine name (or part of the name):").strip()
    
    if user_input:  # Only proceed if the user has entered something
        matches = get_close_matches(user_input, machine_names, n=5, cutoff=0.3)
        
        if matches:
            selected_machine = st.selectbox("Select the correct machine:", matches)
            return selected_machine, data_sheet[data_sheet.iloc[:, 0] == selected_machine]
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
    
    if scenario_choice == "Machine Selection from Excel":
        # Scenario 1: Machine Selection from Excel
        file_path = "Bearing Pressure rev30.xlsx"  # Use relative path
        sheet_name = "Data"
        selected_machine, machine_data = select_machine_from_excel(file_path, sheet_name)
        
        if selected_machine is not None:
            st.write(f"Selected machine: {selected_machine}")
            
            # Perform calculations for each mode
            for index, row in machine_data.iterrows():
                mode = row["MODE"]
                b = row["b"]
                qu = row["qu"]
                L1 = row["L1"]
                
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
                st.write(f"Machine: {selected_machine}, Mode: {mode}, Thicknesses: {thicknesses}")
    
    elif scenario_choice == "Manual Input":
        # Scenario 2: Manual Input
        inputs = get_manual_input()
        
        # Prepare configuration
        cfg = {
            "b": inputs["b"],
            "qu": inputs["qu"],
            "L1": inputs["L1"],
            "platform_phi_k": platform_phi_k[0],
            "platform_gamma_k": 20,
            "gamma_BRECaseNoPlatform": 1.5,
            "gamma_BRECasePlatform": 1.2
        }
        
        # Calculate platform thickness
        thicknesses = calculate_platform_thickness(cfg, subgrade_cu_k_values)
        st.write(f"Platform Thicknesses: {thicknesses}")

# Run the main function
if __name__ == "__main__":
    main()
