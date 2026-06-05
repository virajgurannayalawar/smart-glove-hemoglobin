import psutil
import time


def get_cpu_usage() -> float:
    """
    Returns CPU usage percentage.
    """
    return psutil.cpu_percent(interval=1)


def get_ram_usage() -> float:
    """
    Returns RAM usage percentage.
    """
    memory = psutil.virtual_memory()
    return memory.percent


def get_disk_usage() -> float:
    """
    Returns disk usage percentage.
    """
    disk = psutil.disk_usage('/')
    return disk.percent


def print_system_status():
    """
    Prints current system status.
    """

    cpu = get_cpu_usage()
    ram = get_ram_usage()
    disk = get_disk_usage()

    print("\n========== SYSTEM STATUS ==========")
    print(f"CPU Usage  : {cpu}%")
    print(f"RAM Usage  : {ram}%")
    print(f"Disk Usage : {disk}%")
    print("===================================\n")


if __name__ == "__main__":
    while True:
        print_system_status()
        time.sleep(5)