# GPTboost

A Windows 10 optimization tool designed to eliminate ChatGPT freezes and lag by optimizing system resources for smooth AI interactions.

## Overview

GPTboost tackles common performance issues when running ChatGPT (web and desktop versions) on Windows 10 by:
- Closing resource-heavy background processes
- Clearing browser cache and site data
- Switching to high-performance power mode
- Monitoring system resources
- Providing additional system optimizations

## ⚠️ Warning

**Run this at your own risk.** Optimizations such as these can change settings that might be required by your system. Always create backups and understand the changes before proceeding.

## Installation

### Prerequisites
- Python 3.10 or higher
- Windows 10
- Administrator privileges

### Setup Steps

1. **Install Python 3.10+** from [python.org](https://python.org)

2. **Create and activate virtual environment:**
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Run GPTboost:**
   ```cmd
   python gptboost.py
   ```
   *Note: The script will prompt for admin privileges if not already running as administrator.*

## Usage

### Basic Usage
```cmd
python gptboost.py
```

### Command Line Options
```cmd
# Specify browser for cache clearing
python gptboost.py --browser=edge
python gptboost.py --browser=chrome
python gptboost.py --browser=firefox

# Custom monitoring duration (default: 30 seconds)
python gptboost.py --monitor-duration=60

# Undo previous optimizations
python gptboost.py --undo

# Force admin mode (will restart if needed)
python gptboost.py --admin
```

### What GPTboost Does

1. **Process Optimization**: Closes non-essential background processes like OneDrive, Cortana, SearchApp, and Teams
2. **Browser Cache Clearing**: Removes cached data that can slow down ChatGPT, with special focus on ChatGPT site data
3. **Power Management**: Switches to Windows High Performance mode for better CPU/GPU handling
4. **System Cleanup**: Flushes DNS cache and optimizes startup programs
5. **Resource Monitoring**: Tracks CPU and RAM usage after optimizations
6. **Windows Updates**: Checks for and prompts to install system updates

## Troubleshooting

### Permission Errors
- Ensure you're running as Administrator
- Right-click Command Prompt → "Run as administrator"
- Or use `python gptboost.py --admin` to auto-restart with admin privileges

### Missing Modules
```cmd
# Activate virtual environment first
.venv\Scripts\activate
pip install -r requirements.txt
```

### Persistent ChatGPT Freezes
If issues persist after optimization:
- Check hardware temperatures (CPU/GPU overheating)
- Verify sufficient RAM (8GB+ recommended for ChatGPT)
- Update graphics drivers
- Consider browser extensions that might conflict
- Try different browsers (Edge, Chrome, Firefox)

### Reverting Changes
```cmd
python gptboost.py --undo
```
This will restore your previous power plan and startup program settings.

## Contributing

We welcome contributions! Feel free to:
- Report bugs or suggest features via GitHub issues
- Submit pull requests for improvements
- Share optimization techniques that work well

## License

MIT License - see LICENSE file for details.

---

**⚠️ Important**: Always run GPTboost as Administrator for full functionality. The script includes safety measures and creates backups before making system changes.