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

# Function to select soil type and properties
def get_soil_details():
    st.write("Is the soil cohesive or granular?")
    soil_type = st.radio("Soil Type", ["Cohesive", "Granular"])
    
    if soil_type == "Granular":
        st.error("Currently not accepting granular soil requests.")
        return None, None
    
    st.write("Do you know the soil properties?")
    know_properties = st.radio("Know Properties?", ["Yes", "No"])
    
    if know_properties == "Yes":
        platform_phi_k = st.number_input("Enter platform_phi_k (degrees):", min_value=0.0)
        subgrade_cu_k = st.number_input("Enter subgrade_cu_k (kPa):", min_value=0.0)
        return [platform_phi_k], [subgrade_cu_k]
    
    else:
        st.write("Using default ranges for platform_phi_k and subgrade_cu_k.")
        platform_phi_k = [40, 45, 50, 55]
        subgrade_cu_k = [20, 30, 40, 50, 60]
        return platform_phi_k, subgrade_cu_k

# Function to select machine from Excel
def select_machine_from_excel(file_path, sheet_name, method):
    if not os.path.exists(file_path):
        st.error(f"File not found at: {file_path}")
        return None, None
    
    # Load the Excel file
    data_sheet = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Extract machine names from column `b` (index 1)
    machine_names = data_sheet.iloc[:, 1].dropna().unique().tolist()
    
    # Ask the user to enter the machine name
    user_input = st.text_input("Enter machine name (or part of the name):").strip()
    
    if user_input:
        matches = get_close_matches(user_input, machine_names, n=5, cutoff=0.3)
        if matches:
            selected_machine = st.selectbox("Select the correct machine:", matches)
            return selected_machine, data_sheet[data_sheet.iloc[:, 1] == selected_machine]
        else:
            st.error("No matches found. Please try again.")
            return None, None
    return None, None

# Function to get manual input
def get_manual_input():
    L1 = st.number_input("Enter L1 (mm):", min_value=0.0)
    b = st.number_input("Enter b (mm):", min_value=0.0)
    qu = st.number_input("Enter qu (kPa):", min_value=0.0)
    return {
        "L1": L1,
        "b": b,
        "qu": qu
    }

# Function to get weight range input
def get_weight_range():
    min_weight = st.number_input("Min Weight (kg):", min_value=0.0)
    max_weight = st.number_input("Max Weight (kg):", min_value=0.0)
    return min_weight, max_weight

# Main function
def main():
    st.title("Platform Thickness Calculator")
    
    # Select scenario
    scenario_choice = st.radio("Select scenario:", ["Expert Mode", "Guided Mode"])
    
    if scenario_choice == "Expert Mode":
        # Expert Mode: Direct input fields
        inputs = get_manual_input()
        platform_phi_k, subgrade_cu_k = get_soil_details()
        
        if platform_phi_k and subgrade_cu_k:
            cfg = {
                "b": inputs["b"] / 1000,  # Convert mm to meters
                "qu": inputs["qu"],
                "L1": inputs["L1"] / 1000,  # Convert mm to meters
                "platform_phi_k": platform_phi_k,
                "platform_gamma_k": 20,
                "gamma_BRECaseNoPlatform": 1.5,
                "gamma_BRECasePlatform": 1.2
            }
            
            thicknesses = calculate_platform_thickness(cfg, subgrade_cu_k)
            results = []
            for thickness, comment in thicknesses:
                results.append({
                    "platform_phi_k": platform_phi_k[0],
                    "subgrade_cu_k": subgrade_cu_k[0],
                    "Thickness (m)": round(thickness, 2),
                    "Comment": comment
                })
            
            if results:
                st.dataframe(pd.DataFrame(results))
            else:
                st.write("No results to display.")
    
    elif scenario_choice == "Guided Mode":
        # Guided Mode: Step-by-step questions
        st.write("Do you know the machine details?")
        machine_details = st.radio("Machine Details", ["Yes", "No"])
        
        if machine_details == "No":
            st.error("Please check the machine manual.")
            return
        
        st.write("Select an option:")
        option = st.radio("Options", ["Select Machine from Library", "Enter Machine Details Manually", "Provide Weight Range"])
        
        if option == "Select Machine from Library":
            file_path = "Bearing Pressure rev30.xlsx"
            sheet_name = "Data"
            method = "EN16228"  # Default method
            selected_machine, machine_data = select_machine_from_excel(file_path, sheet_name, method)
            
            if selected_machine:
                st.write(f"Selected machine: {selected_machine}")
                platform_phi_k, subgrade_cu_k = get_soil_details()
                
                if platform_phi_k and subgrade_cu_k:
                    results = []
                    for index, row in machine_data.iterrows():
                        mode = row["MODE"]
                        b = row["b"] / 1000  # Convert mm to meters
                        qu = row["qu"]
                        L1 = row["L1"] / 1000  # Convert mm to meters
                        
                        cfg = {
                            "b": b,
                            "qu": qu,
                            "L1": L1,
                            "platform_phi_k": platform_phi_k[0],
                            "platform_gamma_k": 20,
                            "gamma_BRECaseNoPlatform": 1.5,
                            "gamma_BRECasePlatform": 1.2
                        }
                        
                        thicknesses = calculate_platform_thickness(cfg, subgrade_cu_k)
                        for thickness, comment in thicknesses:
                            results.append({
                                "Machine": selected_machine,
                                "Mode": mode,
                                "platform_phi_k": platform_phi_k[0],
                                "subgrade_cu_k": subgrade_cu_k[0],
                                "Thickness (m)": round(thickness, 2),
                                "Comment": comment
                            })
                    
                    if results:
                        st.dataframe(pd.DataFrame(results))
                    else:
                        st.write("No results to display.")
        
        elif option == "Enter Machine Details Manually":
            inputs = get_manual_input()
            platform_phi_k, subgrade_cu_k = get_soil_details()
            
            if platform_phi_k and subgrade_cu_k:
                cfg = {
                    "b": inputs["b"] / 1000,  # Convert mm to meters
                    "qu": inputs["qu"],
                    "L1": inputs["L1"] / 1000,  # Convert mm to meters
                    "platform_phi_k": platform_phi_k[0],
                    "platform_gamma_k": 20,
                    "gamma_BRECaseNoPlatform": 1.5,
                    "gamma_BRECasePlatform": 1.2
                }
                
                thicknesses = calculate_platform_thickness(cfg, subgrade_cu_k)
                results = []
                for thickness, comment in thicknesses:
                    results.append({
                        "platform_phi_k": platform_phi_k[0],
                        "subgrade_cu_k": subgrade_cu_k[0],
                        "Thickness (m)": round(thickness, 2),
                        "Comment": comment
                    })
                
                if results:
                    st.dataframe(pd.DataFrame(results))
                else:
                    st.write("No results to display.")
        
        elif option == "Provide Weight Range":
            min_weight, max_weight = get_weight_range()
            platform_phi_k, subgrade_cu_k = get_soil_details()
            
            if platform_phi_k and subgrade_cu_k:
                results = []
                for weight in range(int(min_weight), int(max_weight) + 1, 2000):  # Every 2 tonnes
                    cfg = {
                        "b": 1000 / 1000,  # Example value, replace with actual logic
                        "qu": 110,  # Example value, replace with actual logic
                        "L1": 500 / 1000,  # Example value, replace with actual logic
                        "platform_phi_k": platform_phi_k[0],
                        "platform_gamma_k": 20,
                        "gamma_BRECaseNoPlatform": 1.5,
                        "gamma_BRECasePlatform": 1.2
                    }
                    
                    thicknesses = calculate_platform_thickness(cfg, subgrade_cu_k)
                    for thickness, comment in thicknesses:
                        results.append({
                            "Weight (kg)": weight,
                            "platform_phi_k": platform_phi_k[0],
                            "subgrade_cu_k": subgrade_cu_k[0],
                            "Thickness (m)": round(thickness, 2),
                            "Comment": comment
                        })
                
                if results:
                    st.dataframe(pd.DataFrame(results))
                else:
                    st.write("No results to display.")

# Run the main function
if __name__ == "__main__":
    main()
