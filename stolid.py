# stolid.py
"""
Stochastic Load Imbalance Detection (StoLID) Module.
Reference: Section 3.1 & 4 in Banerjee et al. (FGCS 2024).
Classifies active hosts into Overloaded, Underloaded, and Normal states
using Gaussian cumulative distribution functions (CDF).
"""

import math
from config import THETA_OVER, THETA_UNDER, TAU


def standard_normal_cdf(x):
    """Cumulative distribution function for standard normal distribution Phi(x)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def get_host_resource_statistics(host, resource_type):
    """Compute mean mu and standard deviation sigma of aggregate demand (Eq. 6)."""
    total_mu = 0.0
    sum_var = 0.0

    for vm in host.vms.values():
        mu_vm, std_vm = vm.get_stats(resource_type)
        total_mu += mu_vm
        sum_var += (std_vm ** 2)

    total_sigma = math.sqrt(max(sum_var, 1e-6))
    return total_mu, total_sigma


def calculate_overload_probability(host, resource_type):
    """
    Calculate P_over for resource r_k:
    P_over = 1 - Pr(L <= Capacity) = 1 - Phi((Capacity - mu) / sigma) (Eq. 4 & Eq. 6)
    """
    if resource_type == "cpu":
        capacity = host.total_mips
    elif resource_type == "ram":
        capacity = host.total_ram_mb
    elif resource_type == "disk":
        capacity = host.total_storage_mb
    else:
        raise ValueError(f"Unknown resource type: {resource_type}")

    mu, sigma = get_host_resource_statistics(host, resource_type)
    z = (capacity - mu) / sigma
    prob_within_capacity = standard_normal_cdf(z)
    return max(0.0, 1.0 - prob_within_capacity)


def calculate_underload_probability(host, resource_type):
    """
    Calculate P_under for resource r_k:
    P_under = Pr(L <= tau * Capacity) = Phi((tau * Capacity - mu) / sigma) (Eq. 5)
    """
    if resource_type == "cpu":
        capacity = host.total_mips
    elif resource_type == "ram":
        capacity = host.total_ram_mb
    elif resource_type == "disk":
        capacity = host.total_storage_mb
    else:
        raise ValueError(f"Unknown resource type: {resource_type}")

    mu, sigma = get_host_resource_statistics(host, resource_type)
    z = (TAU * capacity - mu) / sigma
    return standard_normal_cdf(z)


def detect_load_imbalance(hosts):
    """
    Partitions active hosts into Overloaded, Underloaded, and Normally-loaded sets.
    Returns:
        overloaded_hosts: list of Host objects (exists r_k: P_over > THETA_OVER)
        underloaded_hosts: list of Host objects (forall r_k: P_under > THETA_UNDER)
        normally_loaded_hosts: list of Host objects
        overloaded_res_map: dict {host_id: [overloaded resource names]}
    """
    overloaded_hosts = []
    underloaded_hosts = []
    normally_loaded_hosts = []
    overloaded_res_map = {}

    resources = ["cpu", "ram", "disk"]

    for host in hosts:
        if not host.is_active or len(host.vms) == 0:
            continue

        p_over = {res: calculate_overload_probability(host, res) for res in resources}
        p_under = {res: calculate_underload_probability(host, res) for res in resources}

        over_resources = [res for res in resources if p_over[res] > THETA_OVER]
        is_underloaded = all(p_under[res] > THETA_UNDER for res in resources)

        if len(over_resources) > 0:
            overloaded_hosts.append(host)
            overloaded_res_map[host.id] = over_resources
        elif is_underloaded:
            underloaded_hosts.append(host)
        else:
            normally_loaded_hosts.append(host)

    return overloaded_hosts, underloaded_hosts, normally_loaded_hosts, overloaded_res_map