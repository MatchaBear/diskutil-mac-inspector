#!/usr/bin/env python3
"""
Enhanced Disk Utilization Inspector for macOS
Analyzes disk space usage discrepancies and provides intelligent file cleanup suggestions

Author: Bernhard Hustomo
Enhanced: June 2025
"""

import subprocess
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import re

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

def parse_file_size(size_str: str) -> int:
    """Parse file size from ls -lh output to bytes"""
    if not size_str:
        return 0
    
    # Handle different size formats (K, M, G, T)
    size_str = size_str.upper().strip()
    multipliers = {'B': 1, 'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
    
    # Extract number and unit
    match = re.match(r'^(\d+\.?\d*)([KMGT]?)$', size_str)
    if match:
        number, unit = match.groups()
        return int(float(number) * multipliers.get(unit, 1))
    return 0

def is_safe_to_delete(filepath: str) -> Tuple[bool, str, str]:
    """
    Determine if a file is safe to delete
    Returns: (is_safe, reason, recommendation)
    """
    filepath = filepath.lower()
    filename = os.path.basename(filepath)
    
    # SAFE TO DELETE
    safe_patterns = [
        # Cache files
        ('/cache/', 'Cache file - safe untuk dihapus', '✅ SAFE'),
        ('/caches/', 'Cache file - safe untuk dihapus', '✅ SAFE'),
        ('.cache', 'Cache file - safe untuk dihapus', '✅ SAFE'),
        
        # Log files (older than current)
        ('.log.', 'Old log file - biasanya safe dihapus', '✅ SAFE'),
        ('.out', 'Output file - kemungkinan safe dihapus', '⚠️ PROBABLY SAFE'),
        
        # Temporary files
        ('/tmp/', 'Temporary file - safe untuk dihapus', '✅ SAFE'),
        ('/temp/', 'Temporary file - safe untuk dihapus', '✅ SAFE'),
        ('.tmp', 'Temporary file - safe untuk dihapus', '✅ SAFE'),
        
        # Download duplicates
        (' (1)', 'Duplicate download - cek dulu sebelum hapus', '⚠️ CHECK FIRST'),
        (' copy', 'Copy file - cek dulu sebelum hapus', '⚠️ CHECK FIRST'),
        
        # Old backups
        ('.bak', 'Backup file - cek umur file dulu', '⚠️ CHECK DATE'),
        ('.backup', 'Backup file - cek umur file dulu', '⚠️ CHECK DATE'),
    ]
    
    # DANGEROUS TO DELETE
    dangerous_patterns = [
        # System files
        ('/system/', 'System file - JANGAN DIHAPUS!', '❌ DANGEROUS'),
        ('/usr/', 'System file - JANGAN DIHAPUS!', '❌ DANGEROUS'),
        ('/bin/', 'System binary - JANGAN DIHAPUS!', '❌ DANGEROUS'),
        ('/sbin/', 'System binary - JANGAN DIHAPUS!', '❌ DANGEROUS'),
        ('/etc/', 'System config - JANGAN DIHAPUS!', '❌ DANGEROUS'),
        
        # Application files
        ('.app/', 'Application - JANGAN DIHAPUS!', '❌ DANGEROUS'),
        ('.framework/', 'Framework - JANGAN DIHAPUS!', '❌ DANGEROUS'),
        
        # Current logs
        ('system.log', 'Active system log - JANGAN DIHAPUS!', '❌ DANGEROUS'),
        ('kernel.log', 'Kernel log - JANGAN DIHAPUS!', '❌ DANGEROUS'),
        
        # User documents
        ('/documents/', 'User document - cek dulu!', '⚠️ USER DATA'),
        ('/desktop/', 'Desktop file - cek dulu!', '⚠️ USER DATA'),
        ('/downloads/', 'Download file - cek dulu!', '⚠️ USER DATA'),
    ]
    
    # Check dangerous patterns first
    for pattern, reason, recommendation in dangerous_patterns:
        if pattern in filepath:
            return False, reason, recommendation
    
    # Check safe patterns
    for pattern, reason, recommendation in safe_patterns:
        if pattern in filepath:
            return True, reason, recommendation
    
    # Default: unknown file
    return False, 'File type tidak dikenal - cek manual dulu', '⚠️ UNKNOWN'

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

def analyze_large_files() -> List[Dict]:
    """Find largest files with detailed info and safety analysis"""
    print("🔍 Analyzing large files and directories...")
    large_files = []
    
    # Commands to find large files with detailed info
    commands = [
        ("System Logs", "sudo find /private/var/log -type f -size +50M -exec ls -lh {} \\; 2>/dev/null"),
        ("System Caches", "sudo find /Library/Caches -type f -size +50M -exec ls -lh {} \\; 2>/dev/null"),
        ("User Caches", "find ~/Library/Caches -type f -size +50M -exec ls -lh {} \\; 2>/dev/null"),
        ("User Downloads", "find ~/Downloads -type f -size +100M -exec ls -lh {} \\; 2>/dev/null"),
        ("Application Support", "find ~/Library/Application\\ Support -type f -size +100M -exec ls -lh {} \\; 2>/dev/null"),
        ("Trash (if accessible)", "find ~/.Trash -type f -size +50M -exec ls -lh {} \\; 2>/dev/null"),
    ]
    
    for category, cmd in commands:
        print(f"   Scanning {category}...")
        output, code = run_command(cmd)
        if code == 0 and output:
            lines = output.strip().split('\n')
            for line in lines:
                if line.strip():
                    # Parse ls -lh output
                    parts = line.split()
                    if len(parts) >= 9:
                        size_str = parts[4]
                        filepath = ' '.join(parts[8:])
                        size_bytes = parse_file_size(size_str)
                        
                        is_safe, reason, recommendation = is_safe_to_delete(filepath)
                        
                        large_files.append({
                            'category': category,
                            'filepath': filepath,
                            'size_human': size_str,
                            'size_bytes': size_bytes,
                            'is_safe': is_safe,
                            'reason': reason,
                            'recommendation': recommendation
                        })
    
    # Sort by size (largest first)
    large_files.sort(key=lambda x: x['size_bytes'], reverse=True)
    return large_files

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

def prompt_file_deletion(large_files: List[Dict]):
    """Interactive prompt to delete files"""
    if not large_files:
        print("   No large files found untuk cleanup.")
        return
    
    print("\n" + "="*70)
    print("🗑️  INTERACTIVE FILE CLEANUP")
    print("="*70)
    
    # Group files by safety level
    safe_files = [f for f in large_files if f['is_safe']]
    unsafe_files = [f for f in large_files if not f['is_safe']]
    
    total_space_safe = sum(f['size_bytes'] for f in safe_files)
    total_space_unsafe = sum(f['size_bytes'] for f in unsafe_files)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Safe to delete: {len(safe_files)} files ({bytes_to_human(total_space_safe)})")
    print(f"   Needs review: {len(unsafe_files)} files ({bytes_to_human(total_space_unsafe)})")
    
    if safe_files:
        print(f"\n✅ SAFE FILES TO DELETE:")
        print(f"{'No':<3} {'Size':<10} {'Category':<15} {'File':<50} {'Status'}")
        print("-" * 90)
        
        for i, file_info in enumerate(safe_files[:10], 1):
            filepath_short = file_info['filepath']
            if len(filepath_short) > 45:
                filepath_short = "..." + filepath_short[-42:]
            
            print(f"{i:<3} {file_info['size_human']:<10} {file_info['category'][:14]:<15} {filepath_short:<50} {file_info['recommendation']}")
        
        if len(safe_files) > 10:
            print(f"... and {len(safe_files) - 10} more files")
        
        print(f"\nTotal space yang bisa dihemat: {bytes_to_human(total_space_safe)}")
        
        while True:
            choice = input(f"\n🤔 Mau delete semua safe files? (y/n/list): ").lower().strip()
            
            if choice == 'y':
                deleted_count = 0
                deleted_size = 0
                
                print("\n🗑️  Deleting safe files...")
                for file_info in safe_files:
                    try:
                        if os.path.exists(file_info['filepath']):
                            os.remove(file_info['filepath'])
                            deleted_count += 1
                            deleted_size += file_info['size_bytes']
                            print(f"   ✅ Deleted: {file_info['filepath']}")
                        else:
                            print(f"   ⚠️  File not found: {file_info['filepath']}")
                    except PermissionError:
                        print(f"   ❌ Permission denied: {file_info['filepath']}")
                    except Exception as e:
                        print(f"   ❌ Error deleting {file_info['filepath']}: {e}")
                
                print(f"\n🎉 CLEANUP COMPLETE!")
                print(f"   Files deleted: {deleted_count}")
                print(f"   Space freed: {bytes_to_human(deleted_size)}")
                break
                
            elif choice == 'n':
                print("   Okay, skipping file deletion.")
                break
                
            elif choice == 'list':
                print(f"\n📋 DETAILED LIST OF SAFE FILES:")
                for i, file_info in enumerate(safe_files, 1):
                    print(f"\n{i}. {file_info['filepath']}")
                    print(f"   Size: {file_info['size_human']}")
                    print(f"   Category: {file_info['category']}")
                    print(f"   Reason: {file_info['reason']}")
            else:
                print("   Please enter 'y', 'n', or 'list'")
    
    if unsafe_files:
        print(f"\n⚠️  FILES THAT NEED MANUAL REVIEW:")
        print(f"{'No':<3} {'Size':<10} {'Category':<15} {'File':<50} {'Status'}")
        print("-" * 90)
        
        for i, file_info in enumerate(unsafe_files[:5], 1):
            filepath_short = file_info['filepath']
            if len(filepath_short) > 45:
                filepath_short = "..." + filepath_short[-42:]
            
            print(f"{i:<3} {file_info['size_human']:<10} {file_info['category'][:14]:<15} {filepath_short:<50} {file_info['recommendation']}")
        
        if len(unsafe_files) > 5:
            print(f"... and {len(unsafe_files) - 5} more files")
        
        print(f"\n⚠️  These files need manual review before deletion!")
        print(f"   Total potential space: {bytes_to_human(total_space_unsafe)}")

def main():
    """Main function to run all disk analysis"""
    print("🚀 Enhanced macOS Disk Utilization Inspector")
    print("=" * 60)
    print("Analyzing disk space dengan intelligent cleanup suggestions...\n")
    
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
    
    # Enhanced large files analysis
    print("6️⃣  ENHANCED LARGE FILES ANALYSIS:")
    large_files = analyze_large_files()
    
    if large_files:
        print(f"\n📊 FOUND {len(large_files)} LARGE FILES:")
        print(f"{'No':<3} {'Size':<10} {'Category':<15} {'Safety':<15} {'File'}")
        print("-" * 80)
        
        for i, file_info in enumerate(large_files[:15], 1):
            filepath_short = file_info['filepath']
            if len(filepath_short) > 40:
                filepath_short = "..." + filepath_short[-37:]
            
            print(f"{i:<3} {file_info['size_human']:<10} {file_info['category'][:14]:<15} {file_info['recommendation']:<15} {filepath_short}")
        
        if len(large_files) > 15:
            print(f"... and {len(large_files) - 15} more files")
        
        # Interactive cleanup
        try:
            prompt_file_deletion(large_files)
        except KeyboardInterrupt:
            print("\n\n⏹️  Cleanup cancelled by user.")
    else:
        print("   No large files found (or insufficient permissions)")
    print()
    
    # Disk list
    print("7️⃣  COMPLETE DISK LIST:")
    disk_list = get_diskutil_list()
    print(disk_list)
    print()
    
    print("📝 ANALYSIS COMPLETE!")
    print("="*60)
    print("This enhanced script helps:")
    print("✅ Identify space discrepancies between df and Finder")
    print("✅ Find large files with size information")
    print("✅ Intelligently categorize files by deletion safety")
    print("✅ Provide interactive cleanup with safety checks")
    print("\nCommon causes of space discrepancies:")
    print("- Time Machine local snapshots")
    print("- iOS device backups")
    print("- Hidden system files and logs")
    print("- APFS space sharing")
    print("- Purgeable/optimized storage")

if __name__ == "__main__":
    main()
