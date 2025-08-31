#!/usr/bin/env python3
"""
GPTboost - Windows 10 Optimization Tool for ChatGPT Performance
Optimizes system resources to reduce ChatGPT freezes and lag.
"""

import os
import sys
import time
import argparse
import logging
import subprocess
import ctypes
import shutil
import winreg
from pathlib import Path
from datetime import datetime
import psutil
import json
import re

if os.name != "nt":
    print("GPTboost is Windows-only.")
    sys.exit(1)


class GPTBoost:
    def __init__(self):
        self.setup_logging()
        log_dir = Path(os.environ.get("LOCALAPPDATA", "~")) / "GPTboost"
        self.backup_file = log_dir / "gptboost_backup.json"
        self.processes_to_close = [
            "OneDrive.exe",
            "Teams.exe",
            "SkypeApp.exe",
            "YourPhone.exe",
            "GameBarPresenceWriter.exe",
            "Xbox.exe",
        ]

    def setup_logging(self):
        """Configure logging to file and console"""
        log_dir = Path(os.environ.get("LOCALAPPDATA", "~")) / "GPTboost"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "gptboost.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
        )
        self.logger = logging.getLogger(__name__)

    def is_admin(self):
        """Check if script is running with administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def restart_as_admin(self):
        """Restart script with administrator privileges"""
        if self.is_admin():
            return True

        self.logger.info("Requesting administrator privileges...")
        try:
            params = " ".join(f'"{a}"' for a in sys.argv[1:])
            rc = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{sys.argv[0]}" {params}', None, 1
            )
            # ShellExecuteW returns >32 on success
            return rc > 32
        except Exception as e:
            self.logger.error(f"Failed to restart as admin: {e}")
            return False

    def close_background_processes(self, dry_run=False):
        """Close non-essential background processes to free resources"""
        self.logger.info("Closing non-essential background processes...")
        safe = set(map(str.lower, self.processes_to_close))
        killed = []
        for proc in psutil.process_iter(["pid", "name"]):
            name = (proc.info["name"] or "").lower()
            if name in safe:
                if dry_run:
                    self.logger.info(
                        f"[DRY RUN] Would close: {name} (pid {proc.info['pid']})"
                    )
                else:
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        proc.kill()
                    killed.append(name)
                    self.logger.info(f"Closed: {name}")
        if not dry_run and not killed:
            self.logger.info("No target processes found running.")

    def detect_main_browser(self):
        """Detect the user's main browser"""
        try:
            # Check default browser from registry
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice",
            ) as key:
                prog_id = winreg.QueryValueEx(key, "ProgId")[0]

            if "Chrome" in prog_id:
                return "chrome"
            elif "Firefox" in prog_id:
                return "firefox"
            elif "Edge" in prog_id or "MSEdge" in prog_id:
                return "edge"
            else:
                return "edge"  # Default fallback
        except:
            return "edge"  # Default fallback

    def _kill_if_running(self, image_names):
        """Kill processes by image name"""
        for name in image_names:
            subprocess.run(["taskkill", "/IM", name, "/F"], capture_output=True)

    def clear_browser_cache(self, browser=None):
        """Clear browser cache with focus on ChatGPT site data"""
        if not browser:
            browser = self.detect_main_browser()

        self.logger.info(f"Clearing {browser} cache and ChatGPT site data...")

        # Kill browser processes first
        self._kill_if_running(
            {
                "chrome": ["chrome.exe"],
                "edge": ["msedge.exe"],
                "firefox": ["firefox.exe"],
                "librewolf": ["librewolf.exe"],
            }.get(browser, [])
        )

        # Collect all relevant cache dirs (multi-profile)
        paths = []
        home = Path.home()
        if browser == "chrome":
            root = home / r"AppData/Local/Google/Chrome/User Data"
            for p in root.glob("*/"):
                paths += [
                    p / "Cache",
                    p / "Code Cache",
                    p / "GPUCache",
                    p / "Service Worker/CacheStorage",
                ]
        elif browser == "edge":
            root = home / r"AppData/Local/Microsoft/Edge/User Data"
            for p in root.glob("*/"):
                paths += [
                    p / "Cache",
                    p / "Code Cache",
                    p / "GPUCache",
                    p / "Service Worker/CacheStorage",
                ]
        elif browser in ("firefox", "librewolf"):
            root = home / (
                r"AppData/Local/Mozilla/Firefox/Profiles"
                if browser == "firefox"
                else r"AppData/Local/LibreWolf/Profiles"
            )
            for prof in root.glob("*/"):
                paths += [prof / "cache2"]

        cleared = 0
        for path in paths:
            try:
                if path.exists():
                    shutil.rmtree(path, ignore_errors=True)
                    cleared += 1
            except Exception as e:
                self.logger.warning(f"Could not clear {path}: {e}")
        self.logger.info(f"Cleared {cleared} cache directories for {browser}")

    def _get_active_scheme_guid(self):
        """Get the GUID of the currently active power scheme"""
        out = subprocess.run(
            ["powercfg", "/getactivescheme"], capture_output=True, text=True
        ).stdout
        m = re.search(r"GUID:\s*([0-9a-fA-F\-]{36})", out)
        return m.group(1) if m else None

    def set_high_performance_mode(self):
        """Switch to Windows High Performance power plan"""
        self.logger.info("Setting High Performance power mode...")
        current = self._get_active_scheme_guid()
        if current:
            self.backup_file.write_text(json.dumps({"power_scheme": current}))
        # Find a high-perf scheme available
        schemes = subprocess.run(
            ["powercfg", "/list"], capture_output=True, text=True
        ).stdout
        high = re.search(
            r"([0-9a-fA-F\-]{36}).*High performance", schemes, re.IGNORECASE
        )
        target = high.group(1) if high else None
        if not target:
            self.logger.warning("High Performance plan not found; staying on current.")
            return current
        subprocess.run(["powercfg", "/setactive", target], check=True)
        self.logger.info("Switched to High Performance.")
        return current

    def flush_dns_cache(self):
        """Flush DNS cache to improve connection speeds"""
        self.logger.info("Flushing DNS cache...")
        try:
            subprocess.run(["ipconfig", "/flushdns"], check=True, capture_output=True)
            self.logger.info("DNS cache flushed successfully")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to flush DNS cache: {e}")

    def monitor_resources(self, duration=30):
        """Monitor CPU and RAM usage after optimizations"""
        self.logger.info(f"Monitoring system resources for {duration} seconds...")

        start_time = time.time()
        cpu_readings = []
        memory_readings = []

        while time.time() - start_time < duration:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent

            cpu_readings.append(cpu_percent)
            memory_readings.append(memory_percent)

            print(f"\rCPU: {cpu_percent:5.1f}% | RAM: {memory_percent:5.1f}%", end="")

        print()  # New line after monitoring

        avg_cpu = sum(cpu_readings) / len(cpu_readings)
        avg_memory = sum(memory_readings) / len(memory_readings)

        self.logger.info(f"Average CPU usage: {avg_cpu:.1f}%")
        self.logger.info(f"Average RAM usage: {avg_memory:.1f}%")

        if avg_cpu > 80 or avg_memory > 80:
            self.logger.warning(
                "High resource usage detected! Consider closing more applications."
            )
        else:
            self.logger.info("Resource usage looks good. Try ChatGPT now!")

    def check_windows_updates(self):
        """Check for Windows updates and prompt user"""
        self.logger.info("Opening Windows Update settings (check manually).")
        subprocess.run(["start", "ms-settings:windowsupdate"], shell=True)

    def optimize_system(self, browser=None, monitor_duration=30, dry_run=False):
        """Run all optimization steps"""
        self.logger.info("Starting GPTboost optimization...")

        # Store original power plan for undo functionality
        original_plan = self.set_high_performance_mode()

        self.close_background_processes(dry_run)
        if not dry_run:
            self.clear_browser_cache(browser)
            self.flush_dns_cache()
            self.check_windows_updates()

        self.logger.info("Optimization complete! Testing system performance...")
        self.monitor_resources(monitor_duration)

        return original_plan

    def undo_optimizations(self):
        """Revert system changes"""
        self.logger.info("Reverting GPTboost optimizations...")
        try:
            if self.backup_file.exists():
                data = json.loads(self.backup_file.read_text())
                guid = data.get("power_scheme")
                if guid:
                    subprocess.run(["powercfg", "/setactive", guid], check=True)
                    self.logger.info(f"Power plan restored to {guid}")
                    return
            self.logger.info("No backup found; leaving current power plan unchanged.")
        except Exception as e:
            self.logger.error(f"Failed to restore power plan: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="GPTboost - Optimize Windows 10 for ChatGPT"
    )
    parser.add_argument(
        "--browser",
        choices=["edge", "chrome", "firefox", "librewolf"],
        help="Specify browser for cache clearing",
    )
    parser.add_argument(
        "--monitor-duration",
        type=int,
        default=30,
        help="Resource monitoring duration in seconds (default: 30)",
    )
    parser.add_argument(
        "--undo", action="store_true", help="Revert previous optimizations"
    )
    parser.add_argument(
        "--admin", action="store_true", help="Force restart as administrator"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying them"
    )

    args = parser.parse_args()

    gptboost = GPTBoost()

    # Check admin privileges
    if not gptboost.is_admin():
        print("GPTboost needs admin for full functionality.")
        if args.admin or input("Restart as administrator? (y/n): ").lower() == "y":
            if gptboost.restart_as_admin():
                sys.exit(0)  # parent exits; elevated child runs
            else:
                sys.exit(1)
        else:
            print("Running with limited functionality...")

    try:
        if args.undo:
            gptboost.undo_optimizations()
        else:
            gptboost.optimize_system(args.browser, args.monitor_duration, args.dry_run)

        print("\nGPTboost completed successfully!")
        print("You can now test ChatGPT performance.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        gptboost.logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
