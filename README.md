# macOS Disk Utilization Inspector 💾

🔍 **Comprehensive disk space analysis tool for MacBook Air M2** - Solves the mystery of why `df -h /` output doesn't match what you see in Finder!

## 🚨 The Problem

Ever noticed that:
- `df -h /` shows different disk usage than Finder?
- Total + Used + Free space doesn't add up correctly?
- Your MacBook seems to have "missing" disk space?

This toolkit helps you understand **exactly** what's consuming your disk space.

## 🧰 Tools Included

### 1. `diskutil_inspector.py` - Comprehensive Analysis
- 📊 Compares `df` vs `diskutil` vs Finder outputs
- 🕵️ Detects hidden files and system usage
- 📦 Analyzes APFS container structure
- 👻 Finds Time Machine local snapshots
- 📱 Checks iOS device backup sizes
- 🔍 Locates large files in common hiding spots
- 💾 Detailed system storage profiling

### 2. `quick_disk_check.sh` - Fast Overview
- ⚡ Quick bash script for immediate insights
- 📋 Shows key disk metrics at a glance
- 🎯 Perfect for daily monitoring

## 🚀 Quick Start

### Fast Check (30 seconds)
```bash
./quick_disk_check.sh
```

### Detailed Analysis (2-3 minutes)
```bash
python3 diskutil_inspector.py
```

## 📊 What You'll Discover

### Common Disk Space "Thieves" on macOS:
1. **Time Machine Local Snapshots** - Can use 10-50GB+ invisibly
2. **iOS Device Backups** - Often 5-20GB per device
3. **System Logs** - Can grow unexpectedly large
4. **APFS Space Sharing** - Multiple volumes sharing same container
5. **Purgeable/Optimized Storage** - Files that can be downloaded again

## 🎯 Perfect For

- **MacBook Air M2 owners** experiencing storage confusion
- **Developers** who need precise disk monitoring
- **macOS users** wanting to understand APFS behavior
- **System administrators** debugging storage issues
- **Anyone** curious about where their disk space really goes

## 💡 Example Scenarios

**Scenario 1:** `df -h /` shows 80% full, but Finder shows 60%
- **Likely cause:** Time Machine snapshots + hidden system files
- **Solution:** Run our analysis to identify and optionally clean

**Scenario 2:** Total + Used + Free ≠ Actual disk size
- **Likely cause:** APFS container with multiple volumes
- **Solution:** Our APFS analysis reveals the true layout

## 🛠️ Requirements

- macOS (tested on MacBook Air M2)
- Python 3.6+ (for detailed analysis)
- Bash (for quick check)
- Some commands require `sudo` for system file access

## 🔒 Privacy & Security

- ✅ No data sent anywhere - runs entirely locally
- ✅ No file modifications - read-only analysis
- ✅ Open source - audit the code yourself
- ⚠️ Some features require sudo for system file access

## 📈 Sample Output

```
🚀 macOS Disk Utilization Inspector
==================================================

1️⃣  DF COMMAND OUTPUT:
   filesystem: /dev/disk3s1s1
   size: 460Gi
   used: 380Gi
   available: 79Gi
   use_percent: 84%

2️⃣  DISKUTIL DETAILED INFO:
   Volume Name: Macintosh HD
   Total Size: 494.4 GB
   Volume Free Space: 85.2 GB
   Volume Used Space: 409.2 GB
   File System: APFS

5️⃣  HIDDEN USAGE ANALYSIS:
   Time Machine Snapshots: 12 found
   Purgeable Space: 15.3 GB
   iOS Backups: 8.2 GB
```

## 🤝 Contributing

Found a bug or have ideas for improvement? Feel free to:
- Open an issue
- Submit a pull request
- Share your disk analysis discoveries!

## 📝 License

MIT License - Feel free to modify and distribute!

---

**Built with ❤️ for fellow MacBook users who want to understand their storage!**
