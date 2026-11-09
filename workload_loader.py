# workload_loader.py
import os
import glob
import math
import numpy as np
import pandas as pd
from config import TOTAL_STEPS

BITBRAINS_STATS = {
    "cpu":    {"mean": 0.0895, "std": 0.0481},
    "memory": {"mean": 0.0957, "std": 0.0393},
    "disk":   {"mean": 0.0361, "std": 0.0174}
}

def get_diurnal_factor(step, total_steps=TOTAL_STEPS):
    """Calibrated diurnal cycle matching Bitbrains realistic business rhythm."""
    hour = (step * 5) / 60.0
    # Modulate between 0.75 (night low) and 1.25 (day peak)
    cycle = 0.5 * (1.0 - math.cos(2.0 * math.pi * (hour - 4.0) / 24.0))
    return 0.75 + 0.50 * cycle

def generate_synthetic_trace(num_vms=5000, steps=TOTAL_STEPS):
    traces = {}
    diurnal_factors = np.array([get_diurnal_factor(s, steps) for s in range(steps)])

    for vm_id in range(num_vms):
        vm_bias = np.random.uniform(0.85, 1.15)
        cpu_base = np.random.normal(BITBRAINS_STATS["cpu"]["mean"], BITBRAINS_STATS["cpu"]["std"], size=steps)
        ram_base = np.random.normal(BITBRAINS_STATS["memory"]["mean"], BITBRAINS_STATS["memory"]["std"], size=steps)
        disk_base = np.random.normal(BITBRAINS_STATS["disk"]["mean"], BITBRAINS_STATS["disk"]["std"], size=steps)

        cpu_mod = cpu_base * diurnal_factors * vm_bias
        ram_mod = ram_base * diurnal_factors * vm_bias
        disk_mod = disk_base * diurnal_factors * vm_bias

        traces[vm_id] = {
            "cpu": np.clip(cpu_mod, 0.01, 0.85),
            "ram": np.clip(ram_mod, 0.01, 0.85),
            "disk": np.clip(disk_mod, 0.01, 0.85)
        }
    return traces

def load_workload_traces(data_dir="data", num_vms=5000, steps=TOTAL_STEPS):
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    if not csv_files:
        print("[WorkloadLoader] No CSV files found in 'data/'. Using calibrated Bitbrains diurnal traces.")
        return generate_synthetic_trace(num_vms=num_vms, steps=steps)
    # Fallback to synthetic if CSV folder is empty
    return generate_synthetic_trace(num_vms=num_vms, steps=steps)