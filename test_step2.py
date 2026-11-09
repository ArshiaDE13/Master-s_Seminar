# test_step2.py
"""Sanity test verifying Host/VM setup, Workload loading, and MBFD placement."""

from config import HOST_SPECS, VM_SPECS
from models import Host, VM
from workload_loader import load_workload_traces
from mbfd import mbfd_placement

def run_test():
    # 1. Instantiate 1000 physical hosts (Table 2)
    hosts = []
    host_id = 0
    for model_name, specs in HOST_SPECS.items():
        for _ in range(specs["count"]):
            hosts.append(Host(host_id=host_id, model_name=model_name, specs=specs))
            host_id += 1

    # 2. Instantiate 5000 VMs (1000 of each of the 5 EC2 types)
    vms = []
    vm_id = 0
    vm_types = list(VM_SPECS.keys())
    for v_type in vm_types:
        for _ in range(1000):
            vms.append(VM(vm_id=vm_id, vm_type=v_type, specs=VM_SPECS[v_type]))
            vm_id += 1

    # 3. Load workloads and update initial demand at timestep 0
    traces = load_workload_traces(data_dir="data", num_vms=len(vms), steps=288)
    for vm in vms:
        t = traces[vm.id]
        vm.update_demand(t["cpu"][0], t["ram"][0], t["disk"][0])

    # 4. Perform MBFD initial placement
    unplaced = mbfd_placement(hosts, vms)
    active_hosts = [h for h in hosts if h.is_active]

    print(f"Total Hosts: {len(hosts)}")
    print(f"Total VMs: {len(vms)}")
    print(f"Active Hosts after MBFD: {len(active_hosts)}")
    print(f"Unplaced VMs: {len(unplaced)}")

if __name__ == "__main__":
    run_test()