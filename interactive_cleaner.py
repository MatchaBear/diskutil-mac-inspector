#!/usr/bin/env python3
"""
Interactive Large File Cleaner for macOS
Finds large files and asks user one-by-one if they want to delete (move to Trash)

Usage: python3 interactive_cleaner.py [min_size_mb]
Example: python3 interactive_cleaner.py 100  # Find files larger than 100MB

Author: Bernhard Hustomo
Created: June 2025
"""

import subprocess
import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import re
from datetime import datetime

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
    
    size_str = size_str.upper().strip()
    multipliers = {'B': 1, 'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
    
    match = re.match(r'^(\d+\.?\d*)([KMGT]?)$', size_str)
    if match:
        number, unit = match.groups()
        return int(float(number) * multipliers.get(unit, 1))
    return 0

def get_file_info(filepath: str) -> Dict:
    """Get detailed file information"""
    try:
        stat = os.stat(filepath)
        modified_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        accessed_time = datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'size_bytes': stat.st_size,
            'size_human': bytes_to_human(stat.st_size),
            'modified': modified_time,
            'accessed': accessed_time,
            'permissions': oct(stat.st_mode)[-3:],
        }
    except Exception as e:
        return {'error': str(e)}

def is_safe_to_delete(filepath: str) -> Tuple[str, str, str]:
    """
    Determine if a file is safe to delete
    Returns: (safety_level, reason, recommendation)
    """
    filepath_lower = filepath.lower()
    filename = os.path.basename(filepath_lower)
    
    # VERY SAFE - Auto-recommend deletion
    very_safe_patterns = [
        ('/cache/', '🟢 Cache file', 'VERY SAFE - biasanya bisa di-regenerate'),
        ('/caches/', '🟢 Cache file', 'VERY SAFE - biasanya bisa di-regenerate'),
        ('.cache', '🟢 Cache file', 'VERY SAFE - biasanya bisa di-regenerate'),
        ('/tmp/', '🟢 Temporary file', 'VERY SAFE - file temporary'),
        ('/temp/', '🟢 Temporary file', 'VERY SAFE - file temporary'),
        ('.tmp', '🟢 Temporary file', 'VERY SAFE - file temporary'),
        ('.log.', '🟢 Old log file', 'VERY SAFE - log file lama'),
    ]
    
    # PROBABLY SAFE - Ask for confirmation
    probably_safe_patterns = [
        ('.dmg', '🟡 Disk image', 'PROBABLY SAFE - installer yang sudah selesai'),
        ('.pkg', '🟡 Package file', 'PROBABLY SAFE - installer yang sudah selesai'),
        ('.zip', '🟡 Archive file', 'PROBABLY SAFE - tapi cek dulu isinya'),
        ('.rar', '🟡 Archive file', 'PROBABLY SAFE - tapi cek dulu isinya'),
        ('.tar', '🟡 Archive file', 'PROBABLY SAFE - tapi cek dulu isinya'),
        (' (1)', '🟡 Duplicate file', 'PROBABLY SAFE - kemungkinan duplicate'),
        (' copy', '🟡 Copy file', 'PROBABLY SAFE - kemungkinan duplicate'),
        ('/.Trashes/', '🟡 Trash file', 'PROBABLY SAFE - file yang sudah di trash'),
    ]
    
    # NEEDS REVIEW - Be careful
    needs_review_patterns = [
        ('/downloads/', '🟠 Download file', 'NEEDS REVIEW - bisa jadi file penting'),
        ('/documents/', '🟠 Document file', 'NEEDS REVIEW - kemungkinan dokumen penting'),
        ('/desktop/', '🟠 Desktop file', 'NEEDS REVIEW - file di desktop'),
        ('.mov', '🟠 Video file', 'NEEDS REVIEW - bisa jadi video penting'),
        ('.mp4', '🟠 Video file', 'NEEDS REVIEW - bisa jadi video penting'),
        ('.mkv', '🟠 Video file', 'NEEDS REVIEW - bisa jadi video penting'),
        ('.avi', '🟠 Video file', 'NEEDS REVIEW - bisa jadi video penting'),
        ('.iso', '🟠 Disk image', 'NEEDS REVIEW - bisa jadi backup penting'),
    ]
    
    # DANGEROUS - Don't recommend deletion
    dangerous_patterns = [
        ('/system/', '🔴 System file', 'DANGEROUS - jangan dihapus!'),
        ('/usr/', '🔴 System file', 'DANGEROUS - jangan dihapus!'),
        ('/bin/', '🔴 System binary', 'DANGEROUS - jangan dihapus!'),
        ('/sbin/', '🔴 System binary', 'DANGEROUS - jangan dihapus!'),
        ('.app/', '🔴 Application', 'DANGEROUS - aplikasi aktif'),
        ('.framework/', '🔴 Framework', 'DANGEROUS - system framework'),
        ('system.log', '🔴 Active log', 'DANGEROUS - log aktif'),
        ('/library/frameworks/', '🔴 System framework', 'DANGEROUS - jangan dihapus!'),
    ]
    
    # Check in order of danger level
    for pattern, reason, recommendation in dangerous_patterns:
        if pattern in filepath_lower:
            return 'DANGEROUS', reason, recommendation
    
    for pattern, reason, recommendation in needs_review_patterns:
        if pattern in filepath_lower:
            return 'NEEDS_REVIEW', reason, recommendation
    
    for pattern, reason, recommendation in probably_safe_patterns:
        if pattern in filepath_lower:
            return 'PROBABLY_SAFE', reason, recommendation
    
    for pattern, reason, recommendation in very_safe_patterns:
        if pattern in filepath_lower:
            return 'VERY_SAFE', reason, recommendation
    
    return 'UNKNOWN', '⚪ Unknown file type', 'UNKNOWN - cek manual dulu'

def move_to_trash(filepath: str) -> bool:
    """Move file to Trash (macOS) instead of permanent deletion"""
    try:
        # Use macOS 'trash' command if available (requires: brew install trash)
        result = subprocess.run(['trash', filepath], capture_output=True)
        if result.returncode == 0:
            return True
        
        # Fallback: Move to ~/.Trash manually
        trash_dir = os.path.expanduser("~/.Trash")
        if not os.path.exists(trash_dir):
            os.makedirs(trash_dir)
        
        filename = os.path.basename(filepath)
        trash_path = os.path.join(trash_dir, filename)
        
        # Handle duplicate names in trash
        counter = 1
        base_name, ext = os.path.splitext(filename)
        while os.path.exists(trash_path):
            new_name = f"{base_name} ({counter}){ext}"
            trash_path = os.path.join(trash_dir, new_name)
            counter += 1
        
        shutil.move(filepath, trash_path)
        return True
        
    except Exception as e:
        print(f"   ❌ Error moving to trash: {e}")
        return False

def find_large_files(min_size_mb: int = 100) -> List[Dict]:
    """Find large files across common locations"""
    print(f"🔍 Searching for files larger than {min_size_mb}MB...")
    large_files = []
    
    # Search locations
    search_locations = [
        ("User Home", f"find ~ -type f -size +{min_size_mb}M 2>/dev/null"),
        ("System Caches", f"sudo find /Library/Caches -type f -size +{min_size_mb}M 2>/dev/null"),
        ("System Logs", f"sudo find /private/var/log -type f -size +{min_size_mb}M 2>/dev/null"),
        ("Applications", f"find /Applications -type f -size +{min_size_mb}M 2>/dev/null"),
    ]
    
    for location_name, cmd in search_locations:
        print(f"   Scanning {location_name}...")
        output, code = run_command(cmd)
        
        if code == 0 and output:
            files = output.strip().split('\n')
            for filepath in files:
                if filepath.strip():
                    file_info = get_file_info(filepath)
                    if 'error' not in file_info:
                        safety_level, reason, recommendation = is_safe_to_delete(filepath)
                        
                        large_files.append({
                            'filepath': filepath,
                            'location': location_name,
                            'size_bytes': file_info['size_bytes'],
                            'size_human': file_info['size_human'],
                            'modified': file_info['modified'],
                            'accessed': file_info['accessed'],
                            'safety_level': safety_level,
                            'reason': reason,
                            'recommendation': recommendation
                        })
    
    # Sort by size (largest first)
    large_files.sort(key=lambda x: x['size_bytes'], reverse=True)
    return large_files

def interactive_cleanup(large_files: List[Dict]):
    """Interactive file-by-file cleanup"""
    if not large_files:
        print("🎉 No large files found!")
        return
    
    print(f"\n📊 Found {len(large_files)} large files")
    print(f"Total size: {bytes_to_human(sum(f['size_bytes'] for f in large_files))}")
    print("\n" + "="*80)
    print("🗑️  INTERACTIVE FILE CLEANUP")
    print("="*80)
    print("Commands: (y)es, (n)o, (s)kip, (i)nfo, (o)pen, (q)uit")
    print("="*80)
    
    deleted_count = 0
    deleted_size = 0
    skipped_count = 0
    
    for i, file_info in enumerate(large_files, 1):
        print(f"\n📄 File {i}/{len(large_files)}")
        print(f"   Path: {file_info['filepath']}")
        print(f"   Size: {file_info['size_human']}")
        print(f"   Safety: {file_info['reason']}")
        print(f"   Recommendation: {file_info['recommendation']}")
        
        # Show default action based on safety level
        if file_info['safety_level'] == 'VERY_SAFE':
            default_action = "y"
            print(f"   💡 Recommended: DELETE (press Enter for yes)")
        elif file_info['safety_level'] == 'PROBABLY_SAFE':
            default_action = "y"
            print(f"   💡 Recommended: DELETE (but double-check)")
        elif file_info['safety_level'] == 'DANGEROUS':
            default_action = "n"
            print(f"   ⚠️  Recommended: KEEP (dangerous to delete)")
        else:
            default_action = "i"
            print(f"   🤔 Recommended: CHECK INFO first")
        
        while True:
            try:
                choice = input(f"\n   Delete this file? [{default_action}]: ").lower().strip()
                if not choice:
                    choice = default_action
                
                if choice in ['y', 'yes']:
                    print(f"   🗑️  Moving to Trash...")
                    if move_to_trash(file_info['filepath']):
                        print(f"   ✅ Moved to Trash successfully!")
                        deleted_count += 1
                        deleted_size += file_info['size_bytes']
                    else:
                        print(f"   ❌ Failed to move to Trash")
                    break
                    
                elif choice in ['n', 'no']:
                    print(f"   ⏭️  Keeping file")
                    break
                    
                elif choice in ['s', 'skip']:
                    print(f"   ⏭️  Skipping file")
                    skipped_count += 1
                    break
                    
                elif choice in ['i', 'info']:
                    print(f"\n   📋 DETAILED INFO:")
                    print(f"      Full path: {file_info['filepath']}")
                    print(f"      Size: {file_info['size_human']} ({file_info['size_bytes']:,} bytes)")
                    print(f"      Modified: {file_info['modified']}")
                    print(f"      Last accessed: {file_info['accessed']}")
                    print(f"      Location: {file_info['location']}")
                    print(f"      Safety level: {file_info['safety_level']}")
                    
                elif choice in ['o', 'open']:
                    print(f"   📂 Opening parent directory...")
                    parent_dir = os.path.dirname(file_info['filepath'])
                    subprocess.run(['open', parent_dir])
                    
                elif choice in ['q', 'quit']:
                    print(f"\n⏹️  Cleanup cancelled by user")
                    return
                    
                else:
                    print(f"   ❓ Invalid choice. Use: y, n, s, i, o, q")
                    
            except KeyboardInterrupt:
                print(f"\n\n⏹️  Cleanup cancelled by user")
                return
    
    # Summary
    print(f"\n" + "="*60)
    print(f"🎉 CLEANUP COMPLETE!")
    print(f"="*60)
    print(f"   Files moved to Trash: {deleted_count}")
    print(f"   Space freed: {bytes_to_human(deleted_size)}")
    print(f"   Files skipped: {skipped_count}")
    print(f"   Files kept: {len(large_files) - deleted_count - skipped_count}")
    
    if deleted_count > 0:
        print(f"\n💡 Tip: Files are in Trash, not permanently deleted.")
        print(f"   You can restore them if needed, or empty Trash to free space permanently.")

def main():
    """Main function"""
    # Parse command line arguments
    min_size_mb = 100  # default
    if len(sys.argv) > 1:
        try:
            min_size_mb = int(sys.argv[1])
        except ValueError:
            print(f"❌ Invalid size: {sys.argv[1]}. Using default 100MB")
    
    print(f"🚀 Interactive Large File Cleaner")
    print(f"Minimum file size: {min_size_mb}MB")
    print(f"Files will be moved to Trash (not permanently deleted)")
    print("="*60)
    
    # Check if 'trash' command is available
    result = subprocess.run(['which', 'trash'], capture_output=True)
    if result.returncode != 0:
        print("💡 Tip: Install 'trash' command for better Trash integration:")
        print("   brew install trash")
        print("   (Using fallback method for now)\n")
    
    # Find large files
    large_files = find_large_files(min_size_mb)
    
    # Interactive cleanup
    interactive_cleanup(large_files)

if __name__ == "__main__":
    main()
