# mbfd.py
import numpy as np
from config import HOST_POWER_PROFILES

def get_power_increase(host, vm):
    current_power = host.get_power_consumption() if host.is_active else 0.0
    new_used_mips = host.used_mips + vm.current_mips_demand
    u_cpu_new = min(new_used_mips / host.total_mips, 1.0)
    
    points = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    power_curve = HOST_POWER_PROFILES[host.model]
    new_power = float(np.interp(u_cpu_new, points, power_curve))
    return new_power - current_power

def is_host_feasible_for_vm(host, vm):
    if (host.used_mips + vm.current_mips_demand) > host.total_mips:
        return False
    if (host.used_ram_mb + vm.current_ram_demand) > host.total_ram_mb:
        return False
    if (host.used_storage_mb + vm.current_storage_demand) > host.total_storage_mb:
        return False
    return True

def mbfd_placement(hosts, vms):
    """Prioritizes power-efficient high-capacity hosts (Dell and Fujitsu)."""
    sorted_vms = sorted(vms, key=lambda x: x.current_mips_demand, reverse=True)
    unplaced_vms = []

    # Sort hosts: Active first, then highest capacity hosts first (descending total_mips)
    candidate_hosts = sorted(hosts, key=lambda h: (not h.is_active, -h.total_mips))

    for vm in sorted_vms:
        allocated_host = None
        min_power_inc = float("inf")

        for host in candidate_hosts:
            if is_host_feasible_for_vm(host, vm):
                p_inc = get_power_increase(host, vm)
                if p_inc < min_power_inc:
                    min_power_inc = p_inc
                    allocated_host = host
                    if host.is_active:
                        break

        if allocated_host is not None:
            allocated_host.vms[vm.id] = vm
            allocated_host.is_active = True
            vm.current_host_id = allocated_host.id
            # Keep candidate list prioritizing already active hosts
            if not allocated_host.is_active:
                candidate_hosts = sorted(hosts, key=lambda h: (not h.is_active, -h.total_mips))
        else:
            unplaced_vms.append(vm)

    return unplaced_vms