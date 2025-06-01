# diskutil-mac-inspector

📦 A personal macOS utility script to inspect APFS volume layout and local Time Machine snapshots using native CLI tools like `diskutil` and `tmutil`.

## 🧰 Features

- Parses and formats `diskutil apfs list` output
- Lists local snapshots from `tmutil listlocalsnapshots /`
- Helps Mac users understand their system volume layout
- Can be used to monitor free space and partition usage

## 📌 Use Case

Useful for:
- Debugging macOS storage space issues
- Learning how APFS containers and volumes work
- Building a portfolio of macOS CLI automation skills

## 🖥️ Example Output

```sh
# diskutil apfs list
# tmutil listlocalsnapshots /

