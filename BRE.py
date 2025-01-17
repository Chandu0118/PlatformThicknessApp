# BRE.py
import numpy as np
from rich import print
import config

def compute_Nγ(platform_phi_k):
    ϕ_prime_rad = np.radians(platform_phi_k)
    term1 = 2 * np.tan(ϕ_prime_rad)
    term2 = np.exp(np.pi * np.tan(ϕ_prime_rad))
    term3 = np.tan(np.radians(45) + 0.5 * ϕ_prime_rad)**2
    Nγ = term1 * (1 + term2 * term3)
    return Nγ

    

def compute_thicknesses_unbewehrt(subgrade_cu_k, cfg):
    Nc = (2 + np.pi)
    sc1 = 1 + 0.2 * (cfg['b'] / cfg['L1'])
    sγ1 = 1 - 0.3 * (cfg['b'] / cfg['L1'])
    sp1 = 1 + (cfg['b'] / cfg['L1'])
    

    Rd1 = subgrade_cu_k * Nc * sc1
    q1d = cfg['gamma_BRECaseNoPlatform'] * cfg['qu']

      

    if Rd1 > q1d:
        print("[green][bold] Rd exceeds q1d. The ground is stable without additional support.[/bold][/green]")
        return np.nan  # Keine Lösung erforderlich, da Rd1 größer als q1d ist

    Nγ_value = compute_Nγ(cfg['platform_phi_k'])
    
    
    platform_strength_1 = 0.5 * cfg['platform_gamma_k'] * cfg['b'] * Nγ_value * sγ1
    q1dP = cfg['gamma_BRECasePlatform'] * cfg['qu']
    
    if q1dP >= platform_strength_1:
        print("[red][bold]BRE: For Case 1: The chosen platform material cannot provide the required bearing resistance. Consider revising the design or materials.[/bold][/red]")
        return np.nan
    
    #print(f" subgrade_cu_k: {subgrade_cu_k}, Rd1: {Rd1}, platform_strength_1: {platform_strength_1}, q1d: {q1d}")
#    print(f"Nγ_value: {Nγ_value}, platform_strength_1: {platform_strength_1}, q1dP: {q1dP}")  # Print-Befehl hinzugefügt
    if Rd1 >= platform_strength_1:
        print("[green][bold]For Case 1: The subgrade is stronger than the platform material.[/bold][/green]")

        return np.nan


    # Berechnung von KptanDELTA
    # Gegebene Werte
    A1 = 2.20708
    A2 = 38.39484
    LOGx01 = 40.54451
    LOGx02 = 51.09954
    h1 = 0.14165
    h2 = 0.16232
    p = 0.16927

    # Funktion zur Berechnung von KptanDELTA
    def calculate_KptanDELTA(platform_phi_k):
        span = A2 - A1
        Section1 = span * p / (1 + np.power(10, (LOGx01 - platform_phi_k) * h1))
        Section2 = span * (1 - p) / (1 + np.power(10, (LOGx02 - platform_phi_k) * h2))
        return A1 + Section1 + Section2
    
    # Berechnung mit gegebenem platform_phi_k
    phi_k = cfg['platform_phi_k']  # Beispielwert, kann angepasst werden
    KptanDELTA = calculate_KptanDELTA(phi_k)
    

    # Berechnung der erforderlichen Plattformdicke für Fall 1
    D1_numerator = cfg['b'] * (q1dP - subgrade_cu_k * Nc * sc1)
    D1_denominator = cfg['platform_gamma_k'] * KptanDELTA * sp1
    D1 = np.sqrt(D1_numerator / D1_denominator) if D1_numerator > 0 else 0.3 
    
    
    D1 = max(0.3, D1)
#   # Prüfen, ob D1 die maximale zulässige Grenze von 1.5 * cfg['b'] überschreitet
    max_allowed_thickness = 1.5 * cfg['b']
        
    if D1 > max_allowed_thickness:
        #print("D1 exceeds the maximum allowed value of 1.5 * cfg['b']")

        # Print the relevant configuration details with a message
        
        #print(f"\033[91mConfiguration {cfg} results in D1 exceeding max allowed value; returning NaN\033[0m")
        #return np.nan  # Oder ein anderer Indikator für kein gültiges Ergebnis
        return D1
    return D1
    

def run(cfg):
    # Filtern der subgrade_cu_k_values, um nur Werte größer als 20 und kleiner als 80 zu behalten
    filtered_subgrade_cu_k_values = [value for value in cfg['subgrade_cu_k_values'] if 20 <= value <= 80]

    # Verwendung der gefilterten Werte für die Berechnungen
    max_thicknesses_unbewehrt = [compute_thicknesses_unbewehrt(value, cfg) for value in filtered_subgrade_cu_k_values]

    return filtered_subgrade_cu_k_values, max_thicknesses_unbewehrt
        
    

if __name__ == "__main__":
    for cfg in config.configurations:
        cfg['subgrade_cu_k_values'] = [value for value in cfg['subgrade_cu_k_values'] if 20 <= value <= 80]
#        print(f"Running configuration: {cfg}")  # Print-Befehl hinzugefügt
        subgrade_cu_k, thicknesses = run(cfg)
#        print(f"Results: subgrade_cu_k: {subgrade_cu_k}, thicknesses: {thicknesses}")  # Print-Befehl hinzugefügt
