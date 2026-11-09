# RO-VMC Reproduction (FGCS 2024)

Python implementation and reproduction of the RO-VMC framework based on:
> **"Towards energy and QoS aware dynamic VM consolidation in a multi-resource cloud"**  
> Sounak Banerjee, Sarbani Roy, Sunirmal Khatua  
> *Future Generation Computer Systems*, Vol. 157, 2024, pp. 376-391.  
> DOI: [10.1016/j.future.2024.03.058](https://doi.org/10.1016/j.future.2024.03.058)

This repository serves as the baseline environment for multi-resource (CPU, RAM, Disk) dynamic VM consolidation across 1,000 heterogeneous physical hosts and 5,000 VMs.

---

## Project Structure

- `config.py` - Datacenter specifications, host profiles (Table 2 & 5), and VM instance types (Table 3).
- `models.py` - Physical host and VM classes with multi-resource utilization tracking.
- `workload_loader.py` - Bitbrains workload generator with calibrated 24-hour diurnal patterns.
- `mbfd.py` - Modified Best Fit Decreasing for initial VM placement.
- `stolid.py` - Stochastic load imbalance detection module using Gaussian CDF (StoLID).
- `rintvmd.py` - Multi-criteria VM selection (MNVMM) and game-based placement (GBVMP) optimized with local delta evaluation.
- `metrics.py` - Evaluation metrics for power, energy, SLATAH, PDM, and SLAV.
- `run_simulation.py` - 24-hour simulation loop across 288 timesteps (5-min intervals).
- `plot_results.py` - Script to generate comparison plots (Figures 2, 3, 5, 6, and 7).

---

## Setup & Dependencies

Ensure Python 3.9+ is installed, then install requirements:

```bash
pip install -r requirements.txt
```

---

## Running the Simulation

Run the 24-hour simulation (288 discrete timesteps):
```bash
python run_simulation.py
```

- Runtime is approximately 7 to 8 minutes on standard modern CPUs.
- Progress, active host counts, instantaneous power, and migration counts are logged in real time.
- Metrics across all timesteps are exported to `simulation_history.json`.

---

## Generating Plots

Generate the evaluation and comparison charts:
```bash
python plot_results.py
```
This produces `ro_vmc_reproduction_results.png`, reproducing Figures 2(a), 3(a), 5(a), 6(a), and 7(a) from the paper.

---

## Simulation Results

Results from a complete 24-hour run under calibrated Bitbrains diurnal load:

| Metric | Reproduced Result | Paper Baseline (Table 6) |
| :--- | :---: | :---: |
| **Total Migrations (24h)** | 1,610 | ~1,545 |
| **VMM / hr** | 67.08 | 64.40 |
| **Average Hourly Power (kW)** | 30.58 | 27.20 |
| **SLATAH (%)** | 5.84% | 2.97% |
| **PDM (%)** | 0.0049% | 0.026% |
| **SLAV** | 0.00000 | 0.078 |

---

## Notes on Computational Optimization

The original GBVMP game formulation evaluates global datacenter preference factors across all candidate hosts for every prospective strategy profile, leading to high computational complexity. 

In this implementation, payoff evaluation is refactored using a **local delta update**:
- Only the source and target host preference factors are updated per trial movement.
- The standard deviation penalty is maintained incrementally in $O(1)$ time.
- Nash equilibrium iterations are bounded to 3 rounds per step.

This preserves the exact mathematical objective of the paper while making full 24-hour simulations practical on standard hardware.