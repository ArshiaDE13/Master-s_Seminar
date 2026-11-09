# models.py
import numpy as np
from config import HOST_POWER_PROFILES

class VM:
    """Represents a Virtual Machine instance and tracks its resource usage history."""
    def __init__(self, vm_id, vm_type, specs):
        self.id = vm_id
        self.vm_type = vm_type
        self.total_mips = specs["cores"] * specs["mips"]
        self.ram_mb = specs["ram_mb"]
        self.storage_mb = specs["storage_mb"]
        
        self.current_mips_demand = 0.0
        self.current_ram_demand = 0.0
        self.current_storage_demand = 0.0
        
        self.history = {"cpu": [], "ram": [], "disk": []}
        self.current_host_id = None

    @property
    def current_disk_demand(self):
        return self.current_storage_demand

    @current_disk_demand.setter
    def current_disk_demand(self, value):
        self.current_storage_demand = value

    def update_demand(self, cpu_ratio, ram_ratio, disk_ratio):
        self.current_mips_demand = cpu_ratio * self.total_mips
        self.current_ram_demand = ram_ratio * self.ram_mb
        self.current_storage_demand = disk_ratio * self.storage_mb
        
        self.history["cpu"].append(self.current_mips_demand)
        self.history["ram"].append(self.current_ram_demand)
        self.history["disk"].append(self.current_storage_demand)
        
        if len(self.history["cpu"]) > 12:
            for k in self.history:
                self.history[k].pop(0)

    def get_stats(self, resource_type):
        hist = self.history[resource_type]
        if len(hist) < 2:
            if resource_type == "cpu":
                val = self.current_mips_demand
            elif resource_type == "ram":
                val = self.current_ram_demand
            else:
                val = self.current_storage_demand
            return val, 1e-4
        return np.mean(hist), max(np.std(hist), 1e-4)


class Host:
    """Represents a Physical Machine (Host) in the cloud data center."""
    def __init__(self, host_id, model_name, specs):
        self.id = host_id
        self.model = model_name
        self.total_mips = specs["cores"] * specs["mips_per_core"]
        self.total_ram_mb = specs["ram_mb"]
        self.total_storage_mb = specs["storage_mb"]
        
        self.vms = {}
        self.is_active = False
        
        self.total_overload_time = 0
        self.total_active_time = 0

    @property
    def used_mips(self):
        return sum(vm.current_mips_demand for vm in self.vms.values())

    @property
    def used_ram_mb(self):
        return sum(vm.current_ram_demand for vm in self.vms.values())

    @property
    def used_storage_mb(self):
        return sum(vm.current_storage_demand for vm in self.vms.values())

    def get_utilization(self):
        """Calculate utilization ratios across all three dimensions (Eq. 2 in paper)."""
        u_cpu = (self.used_mips / self.total_mips) if self.total_mips > 0 else 0.0
        u_ram = (self.used_ram_mb / self.total_ram_mb) if self.total_ram_mb > 0 else 0.0
        u_disk = (self.used_storage_mb / self.total_storage_mb) if self.total_storage_mb > 0 else 0.0
        return {"cpu": u_cpu, "ram": u_ram, "disk": u_disk}

    def get_power_consumption(self):
        """Calculate instantaneous power consumption using SPECpower (Eq. 7)."""
        if not self.is_active or len(self.vms) == 0:
            return 0.0
        
        u_cpu = min(self.get_utilization()["cpu"], 1.0)
        power_curve = HOST_POWER_PROFILES[self.model]
        points = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        return float(np.interp(u_cpu, points, power_curve))