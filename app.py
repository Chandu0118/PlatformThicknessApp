# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 12:53:20 2025

@author: USER
"""

import streamlit as st
import pandas as pd
import numpy as np
from BRE import compute_thicknesses_unbewehrt

# Load the Excel file and generate configurations
def load_and_filter_data():
    file_path = r"C:\Users\USER\Desktop\HIWi\week 10\Platformthicknessapp\Bearing Pressure rev30.xlsx"
    sheet_name = "Data"
    data_sheet = pd.read_excel(file_path, sheet_name=sheet_name)

    # Extract relevant columns (adjust as needed)
    relevant_data = data_sheet.iloc[:, [2, 12, 36, 37]].copy()  # Example: Austrian
    relevant_data.columns = ['MODE', 'b', 'qu', 'L1']

    # Convert columns to numeric
    relevant_data['b'] = pd.to_numeric(relevant_data['b'], errors='coerce')
    relevant_data['qu'] = pd.to_numeric(relevant_data['qu'], errors='coerce')
    relevant_data['L1'] = pd.to_numeric(relevant_data['L1'], errors='coerce')

    # Filter data
    filtered_data = relevant_data[
        (relevant_data['b'] >= 0) &
        (relevant_data['MODE'].str.startswith((''))) &
        (relevant_data['L1'] >= 0) &
        (relevant_data['qu'] >= 110) &
        (relevant_data['L1'] <= 10000)
    ].copy()

    # Drop rows with NaN values
    filtered_data = filtered_data.dropna()

    return filtered_data

# Generate configurations for the web app
def generate_configurations(filtered_data):
    configurations = []
    for index, row in filtered_data.iterrows():
        mode = row['MODE']
        b = round(row['b'] / 1000, 3)  # Convert mm to meters
        qu = round(row['qu'], 3)
        L1 = round(row['L1'] / 1000, 3)  # Convert mm to meters

        configuration = {
            'b': b,
            'L1': L1,
            'platform_gamma_k': 20,
            'platform_phi_k': 50,
            'qu': qu,
            'gamma_BRECaseNoPlatform': 1.5,
            'gamma_BRECasePlatform': 1.2,
            'subgrade_cu_k_values': np.linspace(20, 60, 101)
        }
        configurations.append(configuration)
    return configurations

# Streamlit app
def main():
    st.title("Platform Thickness Calculator")

    # Load and filter data
    filtered_data = load_and_filter_data()

    # Generate configurations
    configurations = generate_configurations(filtered_data)

    # User input: Select machine or enter weight
    option = st.radio("Select input type:", ("Machine Name", "Machine Weight"))

    if option == "Machine Name":
        machine_names = filtered_data['MODE'].tolist()
        selected_machine = st.selectbox("Select a machine", machine_names)

        # Find the configuration for the selected machine
        selected_config = None
        for cfg in configurations:
            if cfg['MODE'] == selected_machine:
                selected_config = cfg
                break

        if selected_config:
            # Compute platform thickness
            thickness = compute_thicknesses_unbewehrt(selected_config['subgrade_cu_k_values'][0], selected_config)
            st.write(f"Platform Thickness: {thickness:.2f} meters")
        else:
            st.write("Machine not found.")
    else:
        machine_weight = st.number_input("Enter machine weight (kg):", min_value=0)
        # Find the closest configuration based on weight (if needed)
        st.write("Feature under development.")

# Run the app
if __name__ == "__main__":
    main()
