#!/usr/bin/env python3
"""
MediaCrawler Analytics Dashboard Startup Script

This script provides easy startup options for the dashboard with different configurations.
"""

import argparse
import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'streamlit', 'plotly', 'seaborn', 'altair', 'pandas', 'numpy'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("All packages installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error installing packages: {e}")
            return False
    
    print("All required packages are installed!")
    return True

def start_dashboard(host='localhost', port=8501, debug=False, auto_open=True):
    """Start the Streamlit dashboard"""
    
    # Check if dashboard.py exists
    dashboard_path = Path(__file__).parent / 'dashboard.py'
    if not dashboard_path.exists():
        print(f"Error: dashboard.py not found at {dashboard_path}")
        return False
    
    # Build command
    cmd = [
        sys.executable, '-m', 'streamlit', 'run',
        str(dashboard_path),
        '--server.headless', 'false',
        '--server.port', str(port),
        '--server.address', host,
        '--browser.gatherUsageStats', 'false'
    ]
    
    if debug:
        cmd.extend(['--logger.level', 'debug'])
    
    print(f"Starting MediaCrawler Analytics Dashboard...")
    print(f"Host: {host}:{port}")
    print(f"Debug mode: {debug}")
    
    try:
        # Start the dashboard
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait a moment for the server to start
        time.sleep(3)
        
        # Check if process started successfully
        if process.poll() is None:
            url = f"http://{host}:{port}"
            print(f"✅ Dashboard started successfully!")
            print(f"🌐 Access the dashboard at: {url}")
            
            if auto_open:
                print("Opening browser...")
                webbrowser.open(url)
            
            try:
                # Wait for the process
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Shutting down dashboard...")
                process.terminate()
                process.wait()
                print("Dashboard stopped.")
            
            return True
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start dashboard")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False
            
    except Exception as e:
        print(f"Error starting dashboard: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='MediaCrawler Analytics Dashboard Startup Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_dashboard.py                    # Start with default settings
  python start_dashboard.py --port 8080       # Use custom port
  python start_dashboard.py --host 0.0.0.0   # Listen on all interfaces
  python start_dashboard.py --debug         # Enable debug mode
  python start_dashboard.py --no-open       # Don't open browser automatically
        """
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='Host address to bind to (default: localhost)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8501,
        help='Port number to use (default: 8501)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    parser.add_argument(
        '--no-open',
        action='store_true',
        help='Don\'t open browser automatically'
    )
    
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Check and install dependencies only'
    )
    
    args = parser.parse_args()
    
    # Check dependencies first
    if not check_dependencies():
        print("❌ Failed to install required dependencies")
        return 1
    
    if args.check_deps:
        print("✅ Dependencies check completed")
        return 0
    
    # Start dashboard
    success = start_dashboard(
        host=args.host,
        port=args.port,
        debug=args.debug,
        auto_open=not args.no_open
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())