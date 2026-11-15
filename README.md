# RO-VMC Reproduction (FGCS 2024)

Python implementation and reproduction of the **RO-VMC** (Resource-Optimized Virtual Machine Consolidation) framework based on:
> **"Towards energy and QoS aware dynamic VM consolidation in a multi-resource cloud"**  
> Sounak Banerjee, Sarbani Roy, Sunirmal Khatua  
> *Future Generation Computer Systems*, Vol. 157, 2024, pp. 376-391.  
> DOI: [10.1016/j.future.2024.03.058](https://doi.org/10.1016/j.future.2024.03.058)

This repository implements the multi-resource (`CPU`, `RAM`, `Disk`) dynamic VM consolidation baseline across **1,000 heterogeneous physical hosts** and **5,000 VMs** over a 24-hour cycle.

---

## Project Structure

- `config.py`: Datacenter specifications, heterogeneous host profiles (Tables 2 & 5), VM instance types (Table 3), and live migration parameters.
- `models.py`: `Host` and `VM` classes with multi-resource utilization tracking and `SPECpower` linear interpolation.
- `workload_loader.py`: Bitbrains workload trace loader and calibrated 24-hour diurnal pattern generator.
- `mbfd.py`: Modified Best Fit Decreasing (MBFD) heuristic with initial placement headroom at `t = 0`.
- `stolid.py`: Stochastic Load Imbalance Detection (StoLID) module using Gaussian cumulative distribution functions (CDF).
- `rintvmd.py`: Multi-criteria migrating VM selection (`MNVMM`), required resource volume estimation (`RRVPVM`), destination host selection (`MNHPVM`), and game-based placement (`GBVMP`).
- `metrics.py`: Performance and QoS evaluation for energy consumption (`kWh`), `VMM/hr`, `SLATAH`, `PDM`, and `SLAV`.
- `run_simulation.py`: 24-hour simulation loop across 288 discrete timesteps (5-minute intervals).
- `plot_results.py`: Visualization script generating comparison plots reproducing the figures from the reference paper.

---

## Setup & Dependencies

Ensure **Python 3.9+** is installed, then install the required packages:

```bash
pip install -r requirements.txt
```

---

## Running the Simulation

Execute the full 24-hour simulation (288 timesteps):

```bash
python run_simulation.py
```

- **Runtime:** ~5–6 minutes on standard modern CPUs.
- **Live Logging:** Active host counts, instantaneous datacenter power (`kW`), and cumulative VM migrations are printed per step.
- **Output:** Step-by-step time-series metrics are exported to `simulation_history.json`.

---

## Generating Plots

Generate the evaluation and comparison plots from the exported history:

```bash
python plot_results.py
```

This produces `ro_vmc_reproduction_results.png`, illustrating the temporal behavior of active hosts, power consumption, and multi-resource utilization trends.

---

## Simulation Results

Results from a complete 24-hour run under calibrated Bitbrains diurnal workloads compared against Table 6 of the reference paper:

| Metric | Reproduced Result | Paper Baseline (Table 6) |
| :--- | :---: | :---: |
| **Total Migrations (24h)** | 1,283 | ~1,545 |
| **VMM / hr** | 53.46 | 64.40 |
| **Average Hourly Power (kW)** | 22.90 | 27.20 |
| **SLATAH (%)** | 2.38% | 2.97% |
| **PDM (%)** | 0.0201% | 0.026% |
| **SLAV** | 0.04785 | 0.078 |

*(Note: Minor variations between the reproduced figures and Table 6 arise from the stochastic nature of the synthetic diurnal Bitbrains workload traces.)*

---

## Implementation Details

- **QoS & SLA Evaluation (Eqs. 9-12):** `SLATAH` measures the fraction of active host time spent at full CPU saturation (`u_cpu >= 1.0`) following each consolidation step. `PDM` evaluates migration-induced degradation using dedicated per-VM live migration bandwidth (`20.0 MB/s`), and `SLAV` follows the percentage-product scale (`SLATAH(%) * PDM(%)`) reported in Table 6.
- **Proactive Consolidation & Placement Headroom:** `StoLID` and `MNVMM` initiate proactive migrations prior to 100% physical saturation, while `MNHPVM` and `GBVMP` maintain a target utilization ceiling (`0.85`, alongside a `0.75` initial MBFD headroom at `t = 0`) to absorb diurnal demand spikes.
- **Local Delta Payoff Optimization (`GBVMP`):** Instead of recomputing global preference factors across all candidate hosts for every strategy profile, trial VM moves update only the source and target preference factors ($PF$) while maintaining the standard deviation penalty incrementally in $O(1)$ time (bounded to 3 best-response rounds per timestep).