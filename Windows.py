#!/usr/bin/env python3 """ windows_bootable_usb.py Creates a bootable USB drive from an ISO image on Windows. Requirements:

Run as Administrator

Python 3.6+

PowerShell available

diskpart, robocopy, bootsect utilities in PATH """ import subprocess import sys import os import tempfile import argparse


def run(cmd, shell=False): """Run a command, printing it first.""" print(f"> {' '.join(cmd) if isinstance(cmd, list) else cmd}") subprocess.check_call(cmd, shell=shell)

def list_physical_disks(): """List physical disks using WMIC.""" result = subprocess.check_output(['wmic', 'diskdrive', 'get', 'DeviceID,Model,Size']) print(result.decode('utf-8', errors='ignore'))

def select_disk(): list_physical_disks() disk_num = input('Enter Disk Number (e.g. 1 for \.\PhysicalDrive1): ').strip() return disk_num

def create_diskpart_script(disk_number, drive_letter): script = f""" select disk {disk_number} clean convert mbr create partition primary format fs=fat32 quick label=BOOTUSB active assign letter={drive_letter} exit """ return script

def run_diskpart(script): """Write and execute a diskpart script.""" with tempfile.NamedTemporaryFile('w', delete=False, suffix='.txt') as f: f.write(script) script_file = f.name try: run(['diskpart', '/s', script_file]) finally: os.remove(script_file)

def mount_iso(iso_path): """Mount ISO with PowerShell and return its drive letter.""" ps = ( f"Mount-DiskImage -ImagePath '{iso_path}'; " f"$vol = Get-DiskImage -ImagePath '{iso_path}' | Get-Volume; " f"$vol.DriveLetter" ) completed = subprocess.check_output(['powershell', '-NoProfile', '-Command', ps], shell=False) drive_letter = completed.decode('utf-8', errors='ignore').strip() if not drive_letter: sys.exit('Failed to mount ISO.') return drive_letter

def dismount_iso(iso_path): """Dismount the ISO.""" run(['powershell', '-NoProfile', '-Command', f"Dismount-DiskImage -ImagePath '{iso_path}'"], shell=False)

def copy_iso_contents(src_drive, dst_drive): """Copy all files from mounted ISO to USB drive.""" src = f"{src_drive}:/" dst = f"{dst_drive}:/" run(['robocopy', src, dst, '/E'])

def install_bootloader(drive_letter): """Make the drive bootable (BIOS+NTLDR/bootmgr).""" run(['bootsect', '/nt60', f"{drive_letter}:"])

def main(): parser = argparse.ArgumentParser(description='Create a bootable USB drive on Windows from ISO.') parser.add_argument('iso', help='Path to the ISO image file') parser.add_argument('-d', '--disk', help='Disk number (as shown by WMIC)', required=False) parser.add_argument('-l', '--letter', help='Drive letter to assign (e.g. R)', default='R') args = parser.parse_args()

if os.name != 'nt':
    sys.exit('This script runs only on Windows.')
if not os.path.isfile(args.iso):
    sys.exit('ISO file not found.')

disk = args.disk or select_disk()
letter = args.letter.upper()

# 1) Partition & format
script = create_diskpart_script(disk, letter)
run_diskpart(script)

# 2) Mount ISO
iso_letter = mount_iso(os.path.abspath(args.iso))

# 3) Copy files
copy_iso_contents(iso_letter, letter)

# 4) Install bootloader
install_bootloader(letter)

# 5) Dismount ISO
dismount_iso(os.path.abspath(args.iso))

print('Bootable USB created successfully!')

if name == 'main': main()

