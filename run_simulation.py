# run_simulation.py
"""
24-hour datacenter simulation loop for RO-VMC reproduction.
Records hourly metric snapshots (Hours 6, 12, 18, 24) to JSON for visualization.
Reference: Section 5 in Banerjee et al. (FGCS 2024).
"""

import sys
import time
import json
import numpy as np
from config import HOST_SPECS, VM_SPECS, TOTAL_STEPS, TIME_STEP_MINUTES
from models import Host, VM
from workload_loader import load_workload_traces
from mbfd import mbfd_placement
from stolid import detect_load_imbalance, calculate_overload_probability
from rintvmd import (
    select_migrating_vms,
    calculate_required_resource_volume,
    select_destination_hosts,
    game_based_vm_placement
)
from metrics import calculate_migration_time, compute_simulation_metrics


def run_full_simulation():
    print("=" * 75)
    print("Starting RO-VMC 24-Hour Simulation (Banerjee et al., FGCS 2024)")
    print("=" * 75)

    hosts = []
    h_id = 0
    for model_name, specs in HOST_SPECS.items():
        for _ in range(specs["count"]):
            h = Host(host_id=h_id, model_name=model_name, specs=specs)
            h.total_energy_kwh = 0.0
            hosts.append(h)
            h_id += 1

    vms = []
    v_id = 0
    for v_type in list(VM_SPECS.keys()):
        for _ in range(1000):
            vm = VM(vm_id=v_id, vm_type=v_type, specs=VM_SPECS[v_type])
            vm.total_mips_requested = 0.0
            vm.total_mips_degraded = 0.0
            vms.append(vm)
            v_id += 1

    traces = load_workload_traces(data_dir="data", num_vms=len(vms), steps=TOTAL_STEPS)

    for vm in vms:
        t = traces[vm.id]
        vm.update_demand(t["cpu"][0], t["ram"][0], t["disk"][0])

    print("[Simulation] Placing 5000 VMs onto hosts using MBFD...")
    unplaced = mbfd_placement(hosts, vms)
    initial_active = sum(1 for h in hosts if h.is_active)
    print(f"[Simulation] Initial placement complete. Active Hosts: {initial_active}")

    total_migrations = 0
    timestep_hours = TIME_STEP_MINUTES / 60.0
    start_time = time.time()

    # Time series storage for plotting
    history_records = {
        "step": [],
        "hour": [],
        "active_hosts": [],
        "power_kw": [],
        "avg_cpu_util": [],
        "avg_ram_util": [],
        "avg_disk_util": [],
        "total_migrations": []
    }

    print("[Simulation] Running 288 timesteps (Live Progress):")

    for step in range(TOTAL_STEPS):
        for vm in vms:
            t = traces[vm.id]
            vm.update_demand(t["cpu"][step], t["ram"][step], t["disk"][step])
            vm.total_mips_requested += vm.current_mips_demand * (TIME_STEP_MINUTES * 60)

        step_active_hosts = 0
        step_power_watts = 0.0
        cpu_utils, ram_utils, disk_utils = [], [], []

        for h in hosts:
            if h.is_active and len(h.vms) > 0:
                h.total_active_time += 1
                step_active_hosts += 1
                p_watts = h.get_power_consumption()
                step_power_watts += p_watts
                h.total_energy_kwh += (p_watts / 1000.0) * timestep_hours

                u = h.get_utilization()
                cpu_utils.append(u["cpu"])
                ram_utils.append(u["ram"])
                disk_utils.append(u["disk"])

                if any(calculate_overload_probability(h, r) > 0.80 for r in ["cpu", "ram", "disk"]):
                    h.total_overload_time += 1
            else:
                h.is_active = False

        hour = (step * TIME_STEP_MINUTES) // 60
        minute = (step * TIME_STEP_MINUTES) % 60

        # Record metrics
        history_records["step"].append(step)
        history_records["hour"].append(hour + minute / 60.0)
        history_records["active_hosts"].append(step_active_hosts)
        history_records["power_kw"].append(step_power_watts / 1000.0)
        history_records["avg_cpu_util"].append(float(np.mean(cpu_utils) * 100.0) if cpu_utils else 0.0)
        history_records["avg_ram_util"].append(float(np.mean(ram_utils) * 100.0) if ram_utils else 0.0)
        history_records["avg_disk_util"].append(float(np.mean(disk_utils) * 100.0) if disk_utils else 0.0)
        history_records["total_migrations"].append(total_migrations)

        # StoLID Detection & RintVMD Consolidation
        active_hosts = [h for h in hosts if h.is_active]
        overloaded, underloaded, normal, over_res_map = detect_load_imbalance(active_hosts)

        if len(overloaded) > 0 or len(underloaded) > 0:
            migrating_vms = select_migrating_vms(overloaded, underloaded, over_res_map)
            if migrating_vms:
                total_migrations += len(migrating_vms)
                for m_vm in migrating_vms:
                    mig_time_sec = calculate_migration_time(m_vm)
                    m_vm.total_mips_degraded += 0.1 * m_vm.current_mips_demand * mig_time_sec

                l_req = calculate_required_resource_volume(migrating_vms)
                idle_hosts = [h for h in hosts if not h.is_active]
                dest_hosts = select_destination_hosts(migrating_vms, normal, idle_hosts, l_req)
                game_based_vm_placement(migrating_vms, dest_hosts)

        # Progress monitor
        elapsed = time.time() - start_time
        progress = (step + 1) / TOTAL_STEPS * 100.0
        sys.stdout.write(
            f"\r  [Step {step+1:03d}/288 | {progress:5.1f}%] "
            f"Time: {hour:02d}:{minute:02d} | "
            f"Active: {step_active_hosts:2d} | "
            f"Power: {step_power_watts/1000.0:5.2f} kW | "
            f"Total Migs: {total_migrations:4d} | "
            f"Elapsed: {elapsed:4.1f}s"
        )
        sys.stdout.flush()

    sys.stdout.write("\n")
    total_time = time.time() - start_time
    print("=" * 75)
    print(f"Simulation Finished in {total_time:.1f} seconds! Results Summary:")
    print("=" * 75)

    results = compute_simulation_metrics(hosts, vms, total_migrations, simulation_hours=24)
    final_active = sum(1 for h in hosts if h.is_active)
    avg_active = float(np.mean(history_records["active_hosts"]))

    print(f"{'Metric':<30} | {'RO-VMC (Our Result)':<20} | {'Paper Table 6 Baseline':<20}")
    print("-" * 75)
    print(f"{'Active Hosts (Average)':<30} | {avg_active:<20.1f} | {'~18.6 (Average)':<20}")
    print(f"{'Active Hosts (Final)':<30} | {final_active:<20} | {'~16 (Hour 24)':<20}")
    print(f"{'Avg Hourly Energy (kW)':<30} | {results['Avg Hourly Energy (kW)']:<20.2f} | {'27.2 kW':<20}")
    print(f"{'Total Migrations (24h)':<30} | {results['Total Migrations']:<20} | {'1545 (approx)':<20}")
    print(f"{'VMM/hr (Migrations/hr)':<30} | {results['VMM/hr']:<20.2f} | {'64.4':<20}")
    print(f"{'SLATAH (%)':<30} | {results['SLATAH (%)']:<20.2f} | {'2.97%':<20}")
    print(f"{'PDM (%)':<30} | {results['PDM (%)']:<20.4f} | {'0.026%':<20}")
    print(f"{'SLAV':<30} | {results['SLAV']:<20.5f} | {'0.078':<20}")
    print("-" * 75)

    # Save history to JSON file
    with open("simulation_history.json", "w") as f:
        json.dump(history_records, f, indent=2)
    print("[Simulation] Time-series history successfully exported to 'simulation_history.json'.")


if __name__ == "__main__":
    run_full_simulation()