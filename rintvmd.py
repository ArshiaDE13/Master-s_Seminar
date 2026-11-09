# rintvmd.py
"""
Resource intensity-aware VM Distribution (RintVMD) Module.
Reference: Section 4.1 & 4.2 in Banerjee et al. (FGCS 2024).
Implements exact Algorithms 1, 2, 3, and 4 (GBVMP) using fast local delta evaluation.
"""

import math
import numpy as np
from config import THETA_OVER, DELTA_INC
from stolid import calculate_overload_probability, standard_normal_cdf


def get_vm_demand_by_resource(vm, resource_name):
    if resource_name == "cpu":
        return vm.current_mips_demand
    elif resource_name == "ram":
        return vm.current_ram_demand
    elif resource_name == "disk":
        return vm.current_storage_demand
    raise ValueError(f"Unknown resource: {resource_name}")


# ============================================================================
# Algorithm 1: MNVMM (Selection of Minimal Number of VMs for Migration)
# ============================================================================

def calculate_resource_weights(host, over_resources):
    """Assign weights to resources on an overloaded host (Eq. 15 in paper)."""
    util = host.get_utilization()
    weights = {}
    for res in ["cpu", "ram", "disk"]:
        u = util[res]
        if res in over_resources:
            weights[res] = 1.0 / max(1.0 - u, 1e-4)
        else:
            weights[res] = max(1.0 - u, 1e-4)
    return weights


def select_migrating_vms(overloaded_hosts, underloaded_hosts, over_res_map):
    """Algorithm 1 (MNVMM): Selects minimal migrating VMs (Lines 1-28)."""
    migrating_vms = []

    # 1. Process Overloaded Hosts
    for host in overloaded_hosts:
        over_res = over_res_map.get(host.id, ["cpu"])
        while any(calculate_overload_probability(host, r) > THETA_OVER for r in ["cpu", "ram", "disk"]):
            if len(host.vms) <= 1:
                break

            weights = calculate_resource_weights(host, over_res)
            active_vms = list(host.vms.values())

            gamma_demands = {}
            for res in ["cpu", "ram", "disk"]:
                demands = [get_vm_demand_by_resource(v, res) for v in active_vms]
                gamma_demands[res] = max(demands) if res in over_res else min(demands)

            min_dist = float("inf")
            best_vm = None

            for vm in active_vms:
                dist_sq = 0.0
                for res in ["cpu", "ram", "disk"]:
                    d_j = get_vm_demand_by_resource(vm, res)
                    diff = d_j - gamma_demands[res]
                    dist_sq += weights[res] * (diff ** 2)

                dist = math.sqrt(dist_sq)
                if dist < min_dist:
                    min_dist = dist
                    best_vm = vm

            if best_vm is not None:
                del host.vms[best_vm.id]
                migrating_vms.append(best_vm)
            else:
                break

    # 2. Process Underloaded Hosts (Full Evacuation - Lines 24-27)
    for host in underloaded_hosts:
        for vm in list(host.vms.values()):
            del host.vms[vm.id]
            migrating_vms.append(vm)
        host.is_active = False

    return migrating_vms


# ============================================================================
# Algorithm 2: RRVPVM (Calculation of Required Resource Volume)
# ============================================================================

def calculate_required_resource_volume(migrating_vms):
    """Algorithm 2 (RRVPVM): Estimates least required capacity L_req."""
    if not migrating_vms:
        return {"cpu": 0.0, "ram": 0.0, "disk": 0.0}

    cum_demand = {
        "cpu": sum(v.current_mips_demand for v in migrating_vms),
        "ram": sum(v.current_ram_demand for v in migrating_vms),
        "disk": sum(v.current_storage_demand for v in migrating_vms)
    }

    l_req = {}
    for res in ["cpu", "ram", "disk"]:
        cap = cum_demand[res]
        sum_var = sum(v.get_stats(res)[1] ** 2 for v in migrating_vms)
        sigma = math.sqrt(max(sum_var, 1e-6))
        
        l_iter = 1
        while True:
            z = (cap - cum_demand[res]) / sigma
            p_over = max(0.0, 1.0 - standard_normal_cdf(z))
            if p_over <= THETA_OVER or l_iter > 50:
                break
            cap += (cap * l_iter * DELTA_INC)
            l_iter += 1
            
        l_req[res] = cap

    return l_req


# ============================================================================
# Algorithm 3: MNHPVM (Selection of Destination Hosts)
# ============================================================================

def select_destination_hosts(migrating_vms, normally_loaded_hosts, idle_hosts, l_req):
    """Algorithm 3 (MNHPVM): Destination host selection (Lines 1-25)."""
    if not migrating_vms:
        return []

    num_migs = len(migrating_vms)
    d_alpha = {
        "cpu": sum(v.current_mips_demand for v in migrating_vms) / num_migs,
        "ram": sum(v.current_ram_demand for v in migrating_vms) / num_migs,
        "disk": sum(v.current_storage_demand for v in migrating_vms) / num_migs
    }

    h_des = []
    h_mat = []

    for host in normally_loaded_hosts:
        h_des.append(host)
        feasible = True
        for res, cap in [("cpu", host.total_mips), ("ram", host.total_ram_mb), ("disk", host.total_storage_mb)]:
            mu = host.used_mips if res == "cpu" else (host.used_ram_mb if res == "ram" else host.used_storage_mb)
            new_mu = mu + d_alpha[res]
            z = (cap - new_mu) / 1e-3
            p_over = max(0.0, 1.0 - standard_normal_cdf(z))
            if p_over > THETA_OVER:
                feasible = False
                break
        if feasible:
            h_mat.append(host)

    j_def = {}
    for res in ["cpu", "ram", "disk"]:
        if res == "cpu":
            avail = sum(h.total_mips - h.used_mips for h in h_mat)
        elif res == "ram":
            avail = sum(h.total_ram_mb - h.used_ram_mb for h in h_mat)
        else:
            avail = sum(h.total_storage_mb - h.used_storage_mb for h in h_mat)
        j_def[res] = max(0.0, l_req[res] - avail)

    if any(val > 0 for val in j_def.values()):
        idle_distances = []
        for h in idle_hosts:
            dist = math.sqrt(
                (h.total_mips - j_def["cpu"]) ** 2 +
                (h.total_ram_mb - j_def["ram"]) ** 2 +
                (h.total_storage_mb - j_def["disk"]) ** 2
            )
            idle_distances.append((dist, h))

        idle_distances.sort(key=lambda x: x[0], reverse=True)

        for _, host in idle_distances:
            h_des.append(host)
            host.is_active = True
            j_def["cpu"] -= host.total_mips
            j_def["ram"] -= host.total_ram_mb
            j_def["disk"] -= host.total_storage_mb
            if all(v <= 0 for v in j_def.values()):
                break

    return h_des


# ============================================================================
# Algorithm 4: GBVMP (Game-Based Virtual Machine Placement)
# ============================================================================

def compute_host_pf(host):
    """Calculates Preference Factor PF_i (Eq. 24)."""
    util = host.get_utilization()
    u_vals = [util["cpu"], util["ram"], util["disk"]]
    gamma = sum(u_vals)
    u_max = max(u_vals)
    delta = sum(u_max - u for u in u_vals)
    return gamma - (delta / 3.0)


def compute_hypothetical_pf(host, vm, mode="add"):
    """
    Computes new PF in O(1) without touching other hosts.
    mode='add' (VM added to target) or mode='remove' (VM removed from source).
    """
    sign = 1.0 if mode == "add" else -1.0
    new_mips = host.used_mips + sign * vm.current_mips_demand
    new_ram = host.used_ram_mb + sign * vm.current_ram_demand
    new_disk = host.used_storage_mb + sign * vm.current_storage_demand

    u_cpu = new_mips / host.total_mips
    u_ram = new_ram / host.total_ram_mb
    u_disk = new_disk / host.total_storage_mb

    if u_cpu > 1.0 or u_ram > 1.0 or u_disk > 1.0:
        return -float("inf")

    u_vals = [u_cpu, u_ram, u_disk]
    gamma = sum(u_vals)
    u_max = max(u_vals)
    delta = sum(u_max - u for u in u_vals)
    return gamma - (delta / 3.0)


def game_based_vm_placement(migrating_vms, destination_hosts):
    """
    Algorithm 4 (GBVMP): Fast Nash Equilibrium Search via local delta payoff updates.
    Calculates exact profile payoff phi_Q = (sum(PF) - std(PF)) * Omega_Q (Eq. 21).
    """
    if not migrating_vms or not destination_hosts:
        return

    # 1. Initial greedy placement based on highest PF improvement
    sorted_vms = sorted(migrating_vms, key=lambda v: v.current_mips_demand, reverse=True)
    for vm in sorted_vms:
        best_h = None
        best_gain = -float("inf")
        for h in destination_hosts:
            pf_new = compute_hypothetical_pf(h, vm, mode="add")
            if pf_new > best_gain:
                best_gain = pf_new
                best_h = h
        if best_h is None:
            best_h = min(destination_hosts, key=lambda h: h.get_utilization()["cpu"])
        best_h.vms[vm.id] = vm
        best_h.is_active = True
        vm.current_host_id = best_h.id

    # 2. Pre-calculate baseline state of destination hosts
    host_idx = {h.id: i for i, h in enumerate(destination_hosts)}
    pf_array = np.array([compute_host_pf(h) for h in destination_hosts], dtype=float)
    m = len(destination_hosts)

    # 3. Game Iterations: VMs play best unilateral response in O(1) per check
    for _ in range(3):
        any_move = False

        for vm in sorted_vms:
            curr_host = next((h for h in destination_hosts if vm.id in h.vms), None)
            if curr_host is None:
                continue

            curr_i = host_idx[curr_host.id]
            curr_pf_old = pf_array[curr_i]
            curr_pf_new = compute_hypothetical_pf(curr_host, vm, mode="remove")

            curr_sum = np.sum(pf_array)
            curr_std = np.std(pf_array)
            best_payoff = curr_sum - curr_std
            best_target = curr_host
            best_target_pf_new = 0.0

            for target_host in destination_hosts:
                if target_host.id == curr_host.id:
                    continue

                target_i = host_idx[target_host.id]
                target_pf_new = compute_hypothetical_pf(target_host, vm, mode="add")
                if target_pf_new == -float("inf"):
                    continue

                if (target_host.used_mips + vm.current_mips_demand > 0.85 * target_host.total_mips or
                    target_host.used_ram_mb + vm.current_ram_demand > 0.85 * target_host.total_ram_mb):
                    continue

                # Local delta evaluation of Eq. 21
                target_pf_old = pf_array[target_i]
                new_sum = curr_sum - curr_pf_old - target_pf_old + curr_pf_new + target_pf_new

                diff_curr = curr_pf_new - curr_pf_old
                diff_target = target_pf_new - target_pf_old
                new_std = math.sqrt(max(0.0, (curr_std ** 2) + ((diff_curr**2 + diff_target**2) / m)))
                new_payoff = new_sum - new_std

                if new_payoff > best_payoff:
                    best_payoff = new_payoff
                    best_target = target_host
                    best_target_pf_new = target_pf_new

            if best_target.id != curr_host.id:
                del curr_host.vms[vm.id]
                best_target.vms[vm.id] = vm
                vm.current_host_id = best_target.id

                pf_array[curr_i] = curr_pf_new
                pf_array[host_idx[best_target.id]] = best_target_pf_new
                any_move = True

        if not any_move:
            break