# config.py
"""
Configuration parameters for cloud datacenter simulation based on:
Banerjee et al., "Towards energy and QoS aware dynamic VM consolidation in a multi-resource cloud"
Future Generation Computer Systems 157 (2024) 376-391.
"""

# General simulation parameters
SIMULATION_HOURS = 24
TIME_STEP_MINUTES = 5
TOTAL_STEPS = (SIMULATION_HOURS * 60) // TIME_STEP_MINUTES  # 288 steps over 24 hours

# Dynamic threshold and control parameters (Section 5.1)
THETA_OVER = 0.80   # Over-utilization threshold (theta_over)
THETA_UNDER = 0.80  # Under-utilization threshold (theta_under)
TAU = 0.30          # Fractional threshold parameter for under-loading (Eq. 5)
DELTA_INC = 0.20    # Capacity increment rate in RRVPVM algorithm (delta)

# Live migration parameters (Section 5.1)
DIRTY_PAGE_MEAN = 0.4        # Mean dirty page memory rate DR (MB/s)
DIRTY_PAGE_STD = 0.2         # Standard deviation of dirty page rate (MB/s)
BANDWIDTH_MIGRATION = 100.0  # Dedicated network bandwidth for migration TR - DR (MB/s)

# Table 2: Physical Machine (Host) configurations
# Heterogeneous datacenter with 5 models, 200 hosts each (total 1000 hosts)
HOST_SPECS = {
    "Hitachi_HA8000": {
        "cores": 4, "mips_per_core": 3067, "ram_mb": 8 * 1024, "storage_mb": 250 * 1024, "count": 200
    },
    "HP_ProLiant_DL580": {
        "cores": 8, "mips_per_core": 2660, "ram_mb": 16 * 1024, "storage_mb": 293.6 * 1024, "count": 200
    },
    "Fujitsu_RX2540": {
        "cores": 36, "mips_per_core": 2300, "ram_mb": 64 * 1024, "storage_mb": 64 * 1024, "count": 200
    },
    "IBM_x3630_M3": {
        "cores": 12, "mips_per_core": 3067, "ram_mb": 12 * 1024, "storage_mb": 160 * 1024, "count": 200
    },
    "Dell_PowerEdge_R7425": {
        "cores": 64, "mips_per_core": 2200, "ram_mb": 128 * 1024, "storage_mb": 120 * 1024, "count": 200
    }
}

# Table 3: Virtual Machine (VM) configurations based on Amazon EC2 instance types
VM_SPECS = {
    "g2.m":    {"cores": 1, "mips": 2300, "ram_mb": 1024, "storage_mb": 3000},
    "g2.xl":   {"cores": 4, "mips": 2300, "ram_mb": 4096, "storage_mb": 3000},
    "m.l":     {"cores": 2, "mips": 2300, "ram_mb": 7808, "storage_mb": 3000},
    "c1.2xl":  {"cores": 8, "mips": 2800, "ram_mb": 7680, "storage_mb": 3000},
    "c2.xl":   {"cores": 4, "mips": 2900, "ram_mb": 3840, "storage_mb": 3000}
}

# Table 5: Host power consumption benchmarks at varying CPU utilization (SPECpower - in Watts)
# CPU Utilization intervals: [0%, 20%, 40%, 60%, 80%, 100%]
HOST_POWER_PROFILES = {
    "Hitachi_HA8000":       [43.5, 58.4, 70.0, 84.5, 107.0, 124.0],
    "HP_ProLiant_DL580":    [520.0, 587.0, 705.0, 766.0, 803.0, 833.0],
    "Fujitsu_RX2540":       [39.0, 98.2, 128.0, 161.0, 216.0, 271.0],
    "IBM_x3630_M3":         [80.2, 133.0, 155.0, 182.0, 217.0, 251.0],
    "Dell_PowerEdge_R7425": [84.9, 154.0, 182.0, 214.0, 253.0, 287.0]
}