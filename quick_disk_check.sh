#!/bin/bash

# Quick Disk Utilization Check for macOS
# Compares df output with actual disk usage to identify discrepancies

echo "🚀 Quick macOS Disk Check"
echo "========================="
echo

echo "📊 DF Command Output:"
df -h /
echo

echo "💾 Diskutil Info (Key Details):"
diskutil info / | grep -E "(Volume Name|Total Size|Volume Free Space|Volume Used Space|File System)"
echo

echo "📦 APFS Container Summary:"
diskutil apfs list | head -20
echo

echo "👻 Time Machine Local Snapshots:"
echo "Number of snapshots: $(tmutil listlocalsnapshots / | wc -l)"
tmutil listlocalsnapshots / | head -5
echo

echo "🔍 Large Files in Common Locations:"
echo "Large files in /var/log:"
sudo find /private/var/log -type f -size +50M -exec ls -lh {} \; 2>/dev/null | head -3
echo
echo "Large cache files:"
find ~/Library/Caches -type f -size +50M -exec ls -lh {} \; 2>/dev/null | head -3
echo

echo "📱 iOS Backup Size:"
if [ -d "$HOME/Library/Application Support/MobileSync/Backup" ]; then
    du -sh "$HOME/Library/Application Support/MobileSync/Backup" 2>/dev/null
else
    echo "No iOS backups found"
fi
echo

echo "📝 Summary:"
echo "If df and Finder show different values, common causes include:"
echo "- Time Machine local snapshots"
echo "- Hidden system files and logs"
echo "- APFS space sharing"
echo "- iOS device backups"
echo "- Optimized/purgeable storage"
echo
echo "Run 'python3 diskutil_inspector.py' for detailed analysis!"

