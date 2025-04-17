import subprocess
import sys
import os
from pathlib import Path

def run(cmd):
    print(f"> {' '.join(cmd)}")
    subprocess.check_call(cmd)

def find_device():
    # Naïve listing — you’d want something more robust (e.g. pyudev)
    print("Available block devices:")
    run(["lsblk", "-o", "NAME,SIZE,MODEL,TRAN"])
    dev = input("Enter the device path (e.g. /dev/sdb): ").strip()
    if not Path(dev).exists():
        sys.exit("Device not found.")
    return dev

def create_partition(dev):
    # Wipe existing
    run(["parted", "--script", dev, "mklabel", "msdos"])
    # Single primary partition, full size
    run(["parted", "--script", dev, "mkpart", "primary", "fat32", "1MiB", "100%"])
    # Set boot flag
    run(["parted", "--script", dev, "set", "1", "boot", "on"])

def format_partition(dev):
    part = dev + "1"
    run(["mkfs.vfat", "-F", "32", part])
    return part

def mount_iso(iso_path, mount_point):
    os.makedirs(mount_point, exist_ok=True)
    run(["mount", "-o", "loop", iso_path, mount_point])

def mount_usb(partition, mount_point):
    os.makedirs(mount_point, exist_ok=True)
    run(["mount", partition, mount_point])

def copy_files(src, dst):
    run(["rsync", "-aH", src + "/", dst + "/"])

def install_grub(device, usb_mount):
    # Assumes BIOS‑style. For UEFI you’d adjust.
    run([
        "grub-install",
        "--target=i386-pc",
        "--boot-directory", os.path.join(usb_mount, "boot"),
        device
    ])

def cleanup(*mount_points):
    for m in mount_points:
        run(["umount", m])

def main():
    if os.geteuid() != 0:
        sys.exit("This script must be run as root.")
    iso = sys.argv[1] if len(sys.argv) > 1 else input("Path to ISO: ").strip()
    if not Path(iso).is_file():
        sys.exit("ISO not found.")
    dev = find_device()
    create_partition(dev)
    part = format_partition(dev)

    iso_mp = "/mnt/iso"
    usb_mp = "/mnt/usb"
    try:
        mount_iso(iso, iso_mp)
        mount_usb(part, usb_mp)
        copy_files(iso_mp, usb_mp)
        install_grub(dev, usb_mp)
    finally:
        cleanup(iso_mp, usb_mp)
        print("Done! You can now safely eject the drive.")

if __name__ == "__main__":
    main()
