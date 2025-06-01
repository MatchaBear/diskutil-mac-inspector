#!/usr/bin/env python3
"""
Disk Utilization Inspector for macOS
Analyzes disk space usage discrepancies between df and Finder on MacBook Air M2

Author: Bernhard Hustomo
Created: June 2025
"""

import subprocess
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

def run_command(cmd: str) -> Tuple[str, int]:
    """Run shell command and return output and exit code"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return f"Error: {e}", 1

def bytes_to_human(bytes_val: int) -> str:
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"

def get_df_info() -> Dict:
    """Get disk usage info from df command"""
    print("📊 Getting disk usage from df...")
    output, _ = run_command("df -h /")
    lines = output.split('\n')
    if len(lines) >= 2:
        data = lines[1].split()
        return {
            'filesystem': data[0],
            'size': data[1],
            'used': data[2],
            'available': data[3],
            'use_percent': data[4],
            'mounted_on': data[5] if len(data) > 5 else data[-1]
        }
    return {}

def get_diskutil_info() -> Dict:
    """Get detailed disk info from diskutil"""
    print("💾 Getting detailed disk info from diskutil...")
    output, _ = run_command("diskutil info /")
    info = {}
    for line in output.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            info[key.strip()] = value.strip()
    return info

def get_diskutil_list() -> str:
    """Get list of all disks"""
    print("📋 Getting disk list...")
    output, _ = run_command("diskutil list")
    return output

def get_storage_overview() -> Dict:
    """Get macOS storage overview using system_profiler"""
    print("🖥️  Getting system storage overview...")
    output, _ = run_command("system_profiler SPStorageDataType -json")
    try:
        data = json.loads(output)
        return data.get('SPStorageDataType', [])
    except json.JSONDecodeError:
        return {}

def get_apfs_info() -> str:
    """Get APFS container info"""
    print("📦 Getting APFS container information...")
    output, _ = run_command("diskutil apfs list")
    return output

def analyze_large_files() -> List[str]:
    """Find largest files that might be hidden from Finder"""
    print("🔍 Analyzing large files and directories...")
    large_files = []
    
    # Check for large files in common locations
    commands = [
        "sudo find /private/var/log -type f -size +100M 2>/dev/null | head -10",
        "sudo find /Library/Caches -type f -size +100M 2>/dev/null | head -10",
        "find ~/Library/Caches -type f -size +100M 2>/dev/null | head -10",
        "find /System/Volumes/Data -name '*.log' -size +100M 2>/dev/null | head -5"
    ]
    
    for cmd in commands:
        output, code = run_command(cmd)
        if code == 0 and output:
            large_files.extend(output.split('\n'))
    
    return [f for f in large_files if f.strip()]

def check_hidden_usage() -> Dict:
    """Check for hidden disk usage"""
    print("👻 Checking for hidden disk usage...")
    hidden_info = {}
    
    # Check Time Machine local snapshots
    output, _ = run_command("tmutil listlocalsnapshots /")
    hidden_info['time_machine_snapshots'] = output.split('\n') if output else []
    
    # Check for purgeable space
    output, _ = run_command("diskutil info / | grep -i purgeable")
    hidden_info['purgeable_info'] = output
    
    # Check mobile device backups
    backup_path = os.path.expanduser("~/Library/Application Support/MobileSync/Backup")
    if os.path.exists(backup_path):
        output, _ = run_command(f"du -sh '{backup_path}' 2>/dev/null")
        hidden_info['ios_backups'] = output
    
    return hidden_info

def get_finder_equivalent() -> str:
    """Get storage info similar to what Finder shows"""
    print("🔍 Getting Finder-equivalent storage info...")
    output, _ = run_command("du -sh / 2>/dev/null")
    return output

def main():
    """Main function to run all disk analysis"""
    print("🚀 macOS Disk Utilization Inspector")
    print("=" * 50)
    print("Analyzing disk space discrepancies between df and Finder...\n")
    
    # Basic df info
    print("1️⃣  DF COMMAND OUTPUT:")
    df_info = get_df_info()
    for key, value in df_info.items():
        print(f"   {key}: {value}")
    print()
    
    # Detailed diskutil info
    print("2️⃣  DISKUTIL DETAILED INFO:")
    diskutil_info = get_diskutil_info()
    important_keys = ['Device Node', 'Volume Name', 'Total Size', 'Volume Free Space', 
                     'Volume Used Space', 'File System', 'APFS Physical Store']
    for key in important_keys:
        if key in diskutil_info:
            print(f"   {key}: {diskutil_info[key]}")
    print()
    
    # APFS info
    print("3️⃣  APFS CONTAINER INFO:")
    apfs_info = get_apfs_info()
    print(apfs_info[:1000] + "..." if len(apfs_info) > 1000 else apfs_info)
    print()
    
    # Storage overview
    print("4️⃣  SYSTEM STORAGE OVERVIEW:")
    storage_data = get_storage_overview()
    if storage_data:
        for volume in storage_data:
            if 'mount_point' in volume and volume['mount_point'] == '/':
                print(f"   Volume: {volume.get('_name', 'Unknown')}")
                print(f"   Free Space: {volume.get('free_space_in_bytes', 'Unknown')}")
                print(f"   Physical Drive Capacity: {volume.get('physical_drive', {}).get('size_in_bytes', 'Unknown')}")
    print()
    
    # Hidden usage analysis
    print("5️⃣  HIDDEN USAGE ANALYSIS:")
    hidden_info = check_hidden_usage()
    
    if hidden_info['time_machine_snapshots']:
        print(f"   Time Machine Snapshots: {len(hidden_info['time_machine_snapshots'])} found")
        for snapshot in hidden_info['time_machine_snapshots'][:3]:
            print(f"     - {snapshot}")
    
    if hidden_info['purgeable_info']:
        print(f"   Purgeable Space: {hidden_info['purgeable_info']}")
    
    if hidden_info.get('ios_backups'):
        print(f"   iOS Backups: {hidden_info['ios_backups']}")
    print()
    
    # Large files analysis
    print("6️⃣  LARGE FILES ANALYSIS:")
    large_files = analyze_large_files()
    if large_files:
        print("   Large files found:")
        for file in large_files[:10]:
            print(f"     - {file}")
    else:
        print("   No large files found (or insufficient permissions)")
    print()
    
    # Disk list
    print("7️⃣  COMPLETE DISK LIST:")
    disk_list = get_diskutil_list()
    print(disk_list)
    print()
    
    print("📝 ANALYSIS COMPLETE!")
    print("="*50)
    print("This script helps identify why df and Finder show different values.")
    print("Common causes:")
    print("- Time Machine local snapshots taking space")
    print("- iOS device backups in ~/Library")
    print("- System and log files not visible in Finder")
    print("- APFS space sharing between volumes")
    print("- Purgeable/optimized storage")

if __name__ == "__main__":
    main()

