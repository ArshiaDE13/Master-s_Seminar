# test_step3.py
"""Sanity test verifying StoLID load imbalance detection on active hosts."""

from config import HOST_SPECS, VM_SPECS
from models import Host, VM
from workload_loader import load_workload_traces
from mbfd import mbfd_placement
from stolid import detect_load_imbalance

def run_test():
    # 1. Setup hosts & VMs
    hosts = []
    h_id = 0
    for model_name, specs in HOST_SPECS.items():
        for _ in range(specs["count"]):
            hosts.append(Host(host_id=h_id, model_name=model_name, specs=specs))
            h_id += 1

    vms = []
    v_id = 0
    for v_type in list(VM_SPECS.keys()):
        for _ in range(1000):
            vms.append(VM(vm_id=v_id, vm_type=v_type, specs=VM_SPECS[v_type]))
            v_id += 1

    # 2. Load workloads
    traces = load_workload_traces(data_dir="data", num_vms=len(vms), steps=288)

    # Simulate 5 past timesteps to populate history for variance estimation
    for step in range(5):
        for vm in vms:
            t = traces[vm.id]
            vm.update_demand(t["cpu"][step], t["ram"][step], t["disk"][step])

    # 3. Initial placement
    mbfd_placement(hosts, vms)
    active_hosts = [h for h in hosts if h.is_active]

    # 4. Run StoLID Detection
    overloaded, underloaded, normal, over_res_map = detect_load_imbalance(active_hosts)

    print("=== StoLID Test Results ===")
    print(f"Total Active Hosts: {len(active_hosts)}")
    print(f"Overloaded Hosts:   {len(overloaded)}")
    print(f"Underloaded Hosts:  {len(underloaded)}")
    print(f"Normally-Loaded:    {len(normal)}")
    if overloaded:
        sample_h = overloaded[0]
        print(f"Sample Overloaded Host #{sample_h.id} Bottlenecks: {over_res_map[sample_h.id]}")

if __name__ == "__main__":
    run_test()