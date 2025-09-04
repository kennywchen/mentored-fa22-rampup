#!/usr/bin/env python3
"""
Service orchestrator that starts and manages all microservices
"""

import subprocess
import time
import signal
import sys
import os
from threading import Thread

class ServiceOrchestrator:
    def __init__(self):
        self.processes = {}
        self.running = True
        
    def start_service(self, name, command, port):
        """Start a microservice"""
        try:
            print(f"Starting {name} on port {port}...")
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes[name] = {
                'process': process,
                'port': port,
                'command': command
            }
            print(f"✅ {name} started (PID: {process.pid})")
            return True
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return False
    
    def start_all_services(self):
        """Start all microservices"""
        services = [
            ("webhook-gateway", ["python", "script.py"], 5000),
            ("processor", ["python", "services/processor.py"], 5001),
            ("agent", ["python", "services/agent.py"], 5002),
            ("git-manager", ["python", "services/gitmanager.py"], 5003),
        ]
        
        for name, command, port in services:
            if not self.start_service(name, command, port):
                print(f"Failed to start {name}, stopping all services...")
                self.stop_all_services()
                return False
            
            # Give service time to start
            time.sleep(2)
        
        print("\n🎉 All services started successfully!")
        print("Services running:")
        for name, info in self.processes.items():
            print(f"  - {name}: http://localhost:{info['port']}")
        
        return True
    
    def stop_all_services(self):
        """Stop all microservices"""
        print("\n🛑 Stopping all services...")
        for name, info in self.processes.items():
            try:
                info['process'].terminate()
                info['process'].wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                info['process'].kill()
                print(f"⚠️  {name} force killed")
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
        
        self.processes.clear()
        print("All services stopped.")
    
    def monitor_services(self):
        """Monitor services and restart if they crash"""
        while self.running:
            time.sleep(10)  # Check every 10 seconds
            
            for name, info in list(self.processes.items()):
                if info['process'].poll() is not None:
                    print(f"⚠️  {name} crashed, restarting...")
                    self.processes.pop(name)
                    self.start_service(name, info['command'], info['port'])
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down...")
        self.running = False
        self.stop_all_services()
        sys.exit(0)

def main():
    orchestrator = ServiceOrchestrator()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, orchestrator.signal_handler)
    signal.signal(signal.SIGTERM, orchestrator.signal_handler)
    
    # Start all services
    if not orchestrator.start_all_services():
        sys.exit(1)
    
    # Start monitoring thread
    monitor_thread = Thread(target=orchestrator.monitor_services)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    try:
        # Keep main thread alive
        while orchestrator.running:
            time.sleep(1)
    except KeyboardInterrupt:
        orchestrator.signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()
