# metrics.py
"""
Performance and QoS evaluation metrics based on:
Section 3.2 & 3.3 in Banerjee et al. (FGCS 2024).
Calculates:
  - Total Energy Consumption (kWh - Eq. 8)
  - SLATAH (SLA violation Time per Active Host - Eq. 9)
  - PDM (Performance Degradation due to Migration - Eq. 10 & 11)
  - SLAV (Combined SLA Violation metric - Eq. 12)
  - VM Migration frequency
"""

import numpy as np
from config import BANDWIDTH_MIGRATION


def calculate_migration_time(vm):
    """
    Estimates migration time for VM v_j (Section 5.1).
    Network bandwidth dedicated to migration is 100 MB/s.
    Migration Time = RAM size (MB) / 100 MB/s.
    """
    return vm.ram_mb / BANDWIDTH_MIGRATION


def compute_simulation_metrics(hosts, vms, total_migrations, simulation_hours=24):
    """
    Aggregates overall simulation statistics matching Table 6 in paper.
    """
    # 1. SLATAH Calculation (Eq. 9): (1 / M) * sum(T_over_i / T_act_i)
    slatah_ratios = []
    total_energy_kwh = 0.0

    for host in hosts:
        if host.total_active_time > 0:
            ratio = host.total_overload_time / host.total_active_time
            slatah_ratios.append(ratio)
        total_energy_kwh += getattr(host, "total_energy_kwh", 0.0)

    slatah = float(np.mean(slatah_ratios)) if slatah_ratios else 0.0

    # 2. PDM Calculation (Eq. 10 & 11): (1 / Z) * sum(R_deg_j / R_req_j)
    pdm_ratios = []
    for vm in vms:
        total_req = getattr(vm, "total_mips_requested", 1.0)
        total_deg = getattr(vm, "total_mips_degraded", 0.0)
        if total_req > 0:
            pdm_ratios.append(total_deg / total_req)

    pdm = float(np.mean(pdm_ratios)) if pdm_ratios else 0.0

    # 3. SLAV Calculation (Eq. 12): SLATAH * PDM
    slav = slatah * pdm

    # 4. Hourly Migration Frequency
    vmm_per_hour = total_migrations / simulation_hours

    return {
        "Total Energy (kWh)": total_energy_kwh,
        "Avg Hourly Energy (kW)": total_energy_kwh / simulation_hours,
        "Total Migrations": total_migrations,
        "VMM/hr": vmm_per_hour,
        "SLATAH (%)": slatah * 100.0,
        "PDM (%)": pdm * 100.0,
        "SLAV": slav
    }