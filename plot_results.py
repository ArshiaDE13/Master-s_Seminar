# plot_results.py
"""
Generates comparison plots matching Figures 2, 3, 5, 6, and 7 from:
Banerjee et al., "Towards energy and QoS aware dynamic VM consolidation in a multi-resource cloud"
Future Generation Computer Systems 157 (2024).
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt

def generate_paper_plots():
    if not os.path.exists("simulation_history.json"):
        print("[Error] 'simulation_history.json' not found. Please run 'python run_simulation.py' first.")
        return

    with open("simulation_history.json", "r") as f:
        data = json.load(f)

    # Step indices corresponding to Hours 6, 12, 18, 24 (Steps 71, 143, 215, 287)
    hour_steps = [71, 143, 215, 287]
    hours_labels = ["6", "12", "18", "24"]

    # Extract sampled metrics at the 4 checkpoint hours
    our_active = [data["active_hosts"][s] for s in hour_steps]
    our_power = [data["power_kw"][s] for s in hour_steps]
    our_cpu = [data["avg_cpu_util"][s] for s in hour_steps]
    our_ram = [data["avg_ram_util"][s] for s in hour_steps]
    our_disk = [data["avg_disk_util"][s] for s in hour_steps]

    # Baseline values reported in the paper (Banerjee et al., Fig 2a, 3a, 5a, 6a, 7a)
    paper_ro_active = [21.0, 20.2, 17.1, 15.8]
    paper_peas_active = [26.2, 24.1, 23.7, 20.7]
    paper_afed_active = [32.4, 31.2, 27.2, 25.4]
    paper_eq_active = [39.3, 38.2, 32.3, 29.8]

    paper_ro_power = [30.7, 28.8, 26.5, 22.8]

    # Set publication plot style
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    x = np.arange(len(hours_labels))
    width = 0.20

    # ----------------------------------------------------
    # Subplot 1: Active Hosts (Replicating Fig. 2a)
    # ----------------------------------------------------
    ax1 = axes[0, 0]
    ax1.bar(x - 1.5 * width, our_active, width, label="Our Reproduced RO-VMC", color="#2563eb")
    ax1.bar(x - 0.5 * width, paper_ro_active, width, label="Paper RO-VMC", color="#38bdf8")
    ax1.bar(x + 0.5 * width, paper_peas_active, width, label="PEAS Baseline", color="#f87171")
    ax1.bar(x + 1.5 * width, paper_eq_active, width, label="EQ-VMC Baseline", color="#9ca3af")
    ax1.set_title("Fig. 2(a): Active Hosts over Time (Bitbrains)", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Time (hr)")
    ax1.set_ylabel("Number of Active Hosts")
    ax1.set_xticks(x)
    ax1.set_xticklabels(hours_labels)
    ax1.set_ylim(0, 45)
    ax1.legend(loc="upper right", fontsize=9)

    # ----------------------------------------------------
    # Subplot 2: Energy Consumption (Replicating Fig. 3a)
    # ----------------------------------------------------
    ax2 = axes[0, 1]
    ax2.bar(x - width/2, our_power, width, label="Our Reproduced RO-VMC", color="#2563eb")
    ax2.bar(x + width/2, paper_ro_power, width, label="Paper RO-VMC", color="#38bdf8")
    ax2.set_title("Fig. 3(a): Hourly Power Consumption (Bitbrains)", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Time (hr)")
    ax2.set_ylabel("Power Consumption (kW)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(hours_labels)
    ax2.set_ylim(0, 45)
    ax2.legend(loc="upper right", fontsize=9)

    # ----------------------------------------------------
    # Subplot 3: CPU & Memory Utilization (Replicating Fig. 5a & 6a)
    # ----------------------------------------------------
    ax3 = axes[1, 0]
    ax3.plot(hours_labels, our_cpu, marker="o", linewidth=2.2, label="CPU Util (%)", color="#dc2626")
    ax3.plot(hours_labels, our_ram, marker="s", linewidth=2.2, label="Memory Util (%)", color="#16a34a")
    ax3.plot(hours_labels, our_disk, marker="^", linewidth=2.2, label="Disk Util (%)", color="#d97706")
    ax3.set_title("Fig. 5(a), 6(a), 7(a): Multi-Resource Utilization", fontsize=12, fontweight="bold")
    ax3.set_xlabel("Time (hr)")
    ax3.set_ylabel("Average Utilization (%)")
    ax3.set_ylim(0, 100)
    ax3.legend(loc="upper right", fontsize=9)

    # ----------------------------------------------------
    # Subplot 4: Continuous 24-Hour Active Hosts & Migrations
    # ----------------------------------------------------
    ax4 = axes[1, 1]
    time_hours = data["hour"]
    ax4.plot(time_hours, data["active_hosts"], color="#1d4ed8", linewidth=2, label="Active Hosts (24h Trend)")
    ax4.set_title("Continuous 24-Hour Active Host Dynamics", fontsize=12, fontweight="bold")
    ax4.set_xlabel("Simulation Hour")
    ax4.set_ylabel("Active Hosts")
    ax4.set_xlim(0, 24)
    ax4.legend(loc="upper right", fontsize=9)

    plt.tight_layout()
    output_png = "ro_vmc_reproduction_results.png"
    plt.savefig(output_png, dpi=300)
    print(f"[Plotting] Reproduction charts successfully saved to '{output_png}'.")

if __name__ == "__main__":
    generate_paper_plots()