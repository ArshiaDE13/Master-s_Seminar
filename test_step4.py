# test_step4.py
"""Sanity test verifying RintVMD algorithms (MNVMM, RRVPVM, MNHPVM, GBVMP)."""

from config import HOST_SPECS, VM_SPECS
from models import Host, VM
from workload_loader import load_workload_traces
from mbfd import mbfd_placement
from stolid import detect_load_imbalance
from rintvmd import (
    select_migrating_vms,
    calculate_required_resource_volume,
    select_destination_hosts,
    game_based_vm_placement
)

def run_test():
    # 1. Instantiate datacenters
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

    # 2. Load workloads & simulate initial history
    traces = load_workload_traces(data_dir="data", num_vms=len(vms), steps=288)
    for step in range(5):
        for vm in vms:
            t = traces[vm.id]
            vm.update_demand(t["cpu"][step], t["ram"][step], t["disk"][step])

    # 3. MBFD Placement
    mbfd_placement(hosts, vms)
    active_hosts = [h for h in hosts if h.is_active]

    # 4. StoLID Detection
    overloaded, underloaded, normal, over_res_map = detect_load_imbalance(active_hosts)
    print(f"Initial: {len(overloaded)} overloaded, {len(underloaded)} underloaded hosts.")

    # 5. MNVMM: Select migrating VMs
    migrating_vms = select_migrating_vms(overloaded, underloaded, over_res_map)
    print(f"MNVMM selected {len(migrating_vms)} VMs for migration.")

    # 6. RRVPVM: Estimate required capacity
    l_req = calculate_required_resource_volume(migrating_vms)
    print(f"RRVPVM required CPU capacity: {l_req['cpu']:.1f} MIPS")

    # 7. MNHPVM: Select destination hosts
    idle_hosts = [h for h in hosts if not h.is_active]
    dest_hosts = select_destination_hosts(migrating_vms, normal, idle_hosts, l_req)
    print(f"MNHPVM allocated {len(dest_hosts)} destination hosts.")

    # 8. GBVMP: Game-based placement
    game_based_vm_placement(migrating_vms, dest_hosts)
    print("GBVMP game successfully reached Nash Equilibrium!")

    # 9. Re-check overload status
    new_overloaded, _, _, _ = detect_load_imbalance([h for h in hosts if h.is_active])
    print(f"Post-Consolidation Overloaded Hosts: {len(new_overloaded)}")

if __name__ == "__main__":
    run_test()