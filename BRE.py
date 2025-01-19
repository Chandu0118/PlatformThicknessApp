# BRE.py
import numpy as np
from rich import print

def compute_Nγ(platform_phi_k):
    """
    Compute the bearing capacity factor Nγ for the given platform_phi_k.
    """
    ϕ_prime_rad = np.radians(platform_phi_k)
    term1 = 2 * np.tan(ϕ_prime_rad)
    term2 = np.exp(np.pi * np.tan(ϕ_prime_rad))
    term3 = np.tan(np.radians(45) + 0.5 * ϕ_prime_rad)**2
    Nγ = term1 * (1 + term2 * term3)
    return Nγ

def compute_thicknesses_unbewehrt(subgrade_cu_k, cfg):
    """
    Compute the required platform thickness for a single configuration.
    """
    Nc = (2 + np.pi)
    sc1 = 1 + 0.2 * (cfg['b'] / cfg['L1'])
    sγ1 = 1 - 0.3 * (cfg['b'] / cfg['L1'])
    sp1 = 1 + (cfg['b'] / cfg['L1'])

    Rd1 = subgrade_cu_k * Nc * sc1
    q1d = cfg['gamma_BRECaseNoPlatform'] * cfg['qu']

    if Rd1 > q1d:
        print("[green][bold] Rd exceeds q1d. The ground is stable without additional support.[/bold][/green]")
        return np.nan  # No solution required, as Rd1 is greater than q1d

    Nγ_value = compute_Nγ(cfg['platform_phi_k'])
    platform_strength_1 = 0.5 * cfg['platform_gamma_k'] * cfg['b'] * Nγ_value * sγ1
    q1dP = cfg['gamma_BRECasePlatform'] * cfg['qu']

    if q1dP >= platform_strength_1:
        print("[red][bold]BRE: For Case 1: The chosen platform material cannot provide the required bearing resistance. Consider revising the design or materials.[/bold][/red]")
        return np.nan

    if Rd1 >= platform_strength_1:
        print("[green][bold]For Case 1: The subgrade is stronger than the platform material.[/bold][/green]")
        return np.nan

    # Calculate KptanDELTA
    def calculate_KptanDELTA(platform_phi_k):
        A1 = 2.20708
        A2 = 38.39484
        LOGx01 = 40.54451
        LOGx02 = 51.09954
        h1 = 0.14165
        h2 = 0.16232
        p = 0.16927

        span = A2 - A1
        Section1 = span * p / (1 + np.power(10, (LOGx01 - platform_phi_k) * h1))
        Section2 = span * (1 - p) / (1 + np.power(10, (LOGx02 - platform_phi_k) * h2))
        return A1 + Section1 + Section2

    KptanDELTA = calculate_KptanDELTA(cfg['platform_phi_k'])

    # Calculate required platform thickness
    D1_numerator = cfg['b'] * (q1dP - subgrade_cu_k * Nc * sc1)
    D1_denominator = cfg['platform_gamma_k'] * KptanDELTA * sp1
    D1 = np.sqrt(D1_numerator / D1_denominator) if D1_numerator > 0 else 0.3
    D1 = max(0.3, D1)

    # Check if D1 exceeds the maximum allowed thickness
    max_allowed_thickness = 1.5 * cfg['b']
    if D1 > max_allowed_thickness:
        return D1  # Return the calculated thickness even if it exceeds the limit

    return D1

def calculate_platform_thickness(cfg, subgrade_cu_k_values):
    """
    Calculate platform thickness for a given configuration and subgrade_cu_k_values.
    """
    thicknesses = []
    for subgrade_cu_k in subgrade_cu_k_values:
        thickness = compute_thicknesses_unbewehrt(subgrade_cu_k, cfg)
        thicknesses.append(thickness)
    return thicknesses