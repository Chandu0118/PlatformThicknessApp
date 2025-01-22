import numpy as np

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
    Returns a tuple: (platform_thickness_in_meters, comment)
    """
    # Check if L1 is zero
    if cfg['L1'] == 0:
        return 0.0, "L1 (platform thickness) cannot be zero."

    Nc = (2 + np.pi)
    sc1 = 1 + 0.2 * (cfg['b'] / cfg['L1'])
    sγ1 = 1 - 0.3 * (cfg['b'] / cfg['L1'])
    sp1 = 1 + (cfg['b'] / cfg['L1'])

    Rd1 = subgrade_cu_k * Nc * sc1
    q1d = cfg['gamma_BRECaseNoPlatform'] * cfg['qu']

    # Case 1: Ground is stable without additional support
    if Rd1 > q1d:
        comment = "Ground is stable without additional support."
        return 0.0, comment  # Return 0.0 as thickness with a comment

    Nγ_value = compute_Nγ(cfg['platform_phi_k'])
    platform_strength_1 = 0.5 * cfg['platform_gamma_k'] * cfg['b'] * Nγ_value * sγ1
    q1dP = cfg['gamma_BRECasePlatform'] * cfg['qu']

    # Case 2: Platform material cannot provide required bearing resistance
    if q1dP >= platform_strength_1:
        comment = "The chosen platform material cannot provide the required bearing resistance. Consider revising the design or materials."
        return 0.0, comment  # Return 0.0 as thickness with a comment

    # Case 3: Subgrade is stronger than the platform material
    if Rd1 >= platform_strength_1:
        comment = "The subgrade is stronger than the platform material."
        return 0.0, comment  # Return 0.0 as thickness with a comment

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

    # Convert np.float64 to plain float
    D1 = float(D1)

    # Check if D1 exceeds the maximum allowed thickness
    max_allowed_thickness = 1.5 * cfg['b']
    if D1 > max_allowed_thickness:
        comment = f"Platform thickness exceeds 1.5 * b (max allowed: {max_allowed_thickness:.2f} m)."
        return D1, comment  # Return the thickness with a comment

    # Default case: Platform thickness is within limits
    comment = "Platform thickness is within limits."
    return D1, comment

def compute_thicknesses_unbewehrt(cfg, subgrade_cu_k_values):
    """
    Calculate platform thickness for a given configuration and subgrade_cu_k_values.
    Returns a list of tuples: [(platform_thickness_in_meters, comment), ...]
    """
    thicknesses = []
    for subgrade_cu_k in subgrade_cu_k_values:
        for platform_phi_k in cfg['platform_phi_k']:
            # Create a new config with a single platform_phi_k value
            cfg_copy = cfg.copy()
            cfg_copy['platform_phi_k'] = platform_phi_k
            thickness, comment = compute_thicknesses_unbewehrt(subgrade_cu_k, cfg_copy)
            thicknesses.append((thickness, comment))
    return thicknesses
