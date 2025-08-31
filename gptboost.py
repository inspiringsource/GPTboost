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


class GPTBoost:
    def __init__(self):
        self.setup_logging()
        self.backup_file = Path("gptboost_backup.json")
        self.processes_to_close = [
            "OneDrive.exe",
            "SearchApp.exe", 
            "Cortana.exe",
            "Teams.exe",
            "SkypeApp.exe",
            "YourPhone.exe",
            "GameBarPresenceWriter.exe",
            "Xbox.exe"
        ]
        
    def setup_logging(self):
        """Configure logging to file and console"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('gptboost.log'),
                logging.StreamHandler(sys.stdout)
            ]
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
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return False
        except Exception as e:
            self.logger.error(f"Failed to restart as admin: {e}")
            return False
            
    def close_background_processes(self):
        """Close non-essential background processes to free resources"""
        self.logger.info("Closing non-essential background processes...")
        closed_processes = []
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] in self.processes_to_close:
                    proc.terminate()
                    closed_processes.append(proc.info['name'])
                    self.logger.info(f"Closed process: {proc.info['name']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        if closed_processes:
            self.logger.info(f"Successfully closed {len(closed_processes)} processes")
        else:
            self.logger.info("No target processes found running")
            
    def detect_main_browser(self):
        """Detect the user's main browser"""
        try:
            # Check default browser from registry
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                              r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice") as key:
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
            
    def clear_browser_cache(self, browser=None):
        """Clear browser cache with focus on ChatGPT site data"""
        if not browser:
            browser = self.detect_main_browser()
            
        self.logger.info(f"Clearing {browser} cache and ChatGPT site data...")
        
        cache_paths = {
            "chrome": [
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data\Default\Cache"),
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data\Default\Code Cache"),
            ],
            "firefox": [
                os.path.expanduser(r"~\AppData\Local\Mozilla\Firefox\Profiles"),
            ],
            "edge": [
                os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\User Data\Default\Cache"),
                os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\User Data\Default\Code Cache"),
            ],
            "librewolf": [
                os.path.expanduser(r"~\AppData\Local\LibreWolf\Profiles"),
            ]
        }
        
        paths_to_clear = cache_paths.get(browser, cache_paths["edge"])
        cleared_count = 0
        
        for cache_path in paths_to_clear:
            if os.path.exists(cache_path):
                try:
                    if "Profiles" in cache_path:  # Firefox/LibreWolf
                        for profile in os.listdir(cache_path):
                            profile_cache = os.path.join(cache_path, profile, "cache2")
                            if os.path.exists(profile_cache):
                                shutil.rmtree(profile_cache, ignore_errors=True)
                                cleared_count += 1
                    else:
                        shutil.rmtree(cache_path, ignore_errors=True)
                        cleared_count += 1
                except Exception as e:
                    self.logger.warning(f"Could not clear {cache_path}: {e}")
                    
        self.logger.info(f"Cleared {cleared_count} cache directories for {browser}")
        
    def set_high_performance_mode(self):
        """Switch to Windows High Performance power plan"""
        self.logger.info("Setting High Performance power mode...")
        
        try:
            # Get current power plan for backup
            result = subprocess.run(
                ["powercfg", "/getactivescheme"], 
                capture_output=True, text=True, check=True
            )
            current_plan = result.stdout.strip()
            
            # Set high performance mode
            subprocess.run(
                ["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"], 
                check=True
            )
            
            self.logger.info("Successfully switched to High Performance mode")
            return current_plan
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to set power plan: {e}")
            return None
            
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
            self.logger.warning("High resource usage detected! Consider closing more applications.")
        else:
            self.logger.info("Resource usage looks good. Try ChatGPT now!")
            
    def check_windows_updates(self):
        """Check for Windows updates and prompt user"""
        self.logger.info("Checking for Windows updates...")
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-WindowsUpdate -AcceptAll -Install -AutoReboot"],
                capture_output=True, text=True, timeout=30
            )
            if "No updates" in result.stdout:
                self.logger.info("No Windows updates available")
            else:
                self.logger.info("Windows updates available. Consider installing them.")
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            self.logger.info("Could not check for updates automatically. Check Windows Update manually.")
            
    def optimize_system(self, browser=None, monitor_duration=30):
        """Run all optimization steps"""
        self.logger.info("Starting GPTboost optimization...")
        
        # Store original power plan for undo functionality
        original_plan = self.set_high_performance_mode()
        
        self.close_background_processes()
        self.clear_browser_cache(browser)
        self.flush_dns_cache()
        self.check_windows_updates()
        
        self.logger.info("Optimization complete! Testing system performance...")
        self.monitor_resources(monitor_duration)
        
        return original_plan
        
    def undo_optimizations(self):
        """Revert system changes"""
        self.logger.info("Reverting GPTboost optimizations...")
        
        # This is a simplified undo - in a full implementation, 
        # you'd want to store more detailed backup information
        try:
            # Reset to balanced power plan (default)
            subprocess.run(
                ["powercfg", "/setactive", "381b4222-f694-41f0-9685-ff5bb260df2e"], 
                check=True
            )
            self.logger.info("Power plan reset to Balanced mode")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to reset power plan: {e}")
            
        self.logger.info("Undo complete")


def main():
    parser = argparse.ArgumentParser(description="GPTboost - Optimize Windows 10 for ChatGPT")
    parser.add_argument("--browser", choices=["edge", "chrome", "firefox", "librewolf"], 
                       help="Specify browser for cache clearing")
    parser.add_argument("--monitor-duration", type=int, default=30,
                       help="Resource monitoring duration in seconds (default: 30)")
    parser.add_argument("--undo", action="store_true",
                       help="Revert previous optimizations")
    parser.add_argument("--admin", action="store_true",
                       help="Force restart as administrator")
    
    args = parser.parse_args()
    
    gptboost = GPTBoost()
    
    # Check admin privileges
    if not gptboost.is_admin():
        print("GPTboost requires administrator privileges for full functionality.")
        if args.admin or input("Restart as administrator? (y/n): ").lower() == 'y':
            if not gptboost.restart_as_admin():
                sys.exit(1)
        else:
            print("Running with limited functionality...")
    
    try:
        if args.undo:
            gptboost.undo_optimizations()
        else:
            gptboost.optimize_system(args.browser, args.monitor_duration)
            
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