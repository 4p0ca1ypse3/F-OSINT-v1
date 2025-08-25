"""
Tor network handler for F-OSINT DWv1
"""

import os
import time
import subprocess
import threading
from typing import Optional, Dict, Any

import stem
from stem import Signal
from stem.control import Controller
from stem.process import launch_tor_with_config

from utils.networking import TorSession, check_tor_service


class TorHandler:
    """Tor network handler"""
    
    def __init__(self, socks_port: int = 9050, control_port: int = 9051):
        self.socks_port = socks_port
        self.control_port = control_port
        self.tor_process = None
        self.controller = None
        self.session = None
        self.is_running = False
        
    def start_tor(self, config_file: str = None) -> bool:
        """Start Tor service"""
        try:
            # Check if Tor is already running
            if check_tor_service('127.0.0.1', self.socks_port):
                self.is_running = True
                self._connect_controller()
                self._create_session()
                return True
            
            # Launch Tor with configuration
            tor_config = {
                'SocksPort': str(self.socks_port),
                'ControlPort': str(self.control_port),
                'CookieAuthentication': '1',
                'ExitPolicy': 'reject *:*'
            }
            
            if config_file and os.path.exists(config_file):
                # Use custom config file
                self.tor_process = subprocess.Popen([
                    'tor', '-f', config_file
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                # Use built-in config
                self.tor_process = launch_tor_with_config(
                    config=tor_config,
                    timeout=60
                )
            
            # Wait for Tor to start
            time.sleep(5)
            
            # Connect to controller
            if self._connect_controller():
                self._create_session()
                self.is_running = True
                return True
                
        except Exception as e:
            print(f"Error starting Tor: {e}")
            
        return False
    
    def stop_tor(self):
        """Stop Tor service"""
        try:
            if self.controller:
                self.controller.close()
                self.controller = None
            
            if self.tor_process:
                self.tor_process.terminate()
                self.tor_process.wait(timeout=10)
                self.tor_process = None
            
            self.session = None
            self.is_running = False
            
        except Exception as e:
            print(f"Error stopping Tor: {e}")
    
    def _connect_controller(self) -> bool:
        """Connect to Tor controller"""
        try:
            self.controller = Controller.from_port(port=self.control_port)
            self.controller.authenticate()
            return True
        except Exception as e:
            print(f"Error connecting to Tor controller: {e}")
            return False
    
    def _create_session(self):
        """Create Tor session"""
        self.session = TorSession(proxy_port=self.socks_port)
    
    def get_session(self) -> Optional[TorSession]:
        """Get Tor session"""
        return self.session if self.is_running else None
    
    def new_identity(self) -> bool:
        """Request new Tor identity"""
        try:
            if self.controller:
                self.controller.signal(Signal.NEWNYM)
                time.sleep(5)  # Wait for new circuit
                return True
        except Exception as e:
            print(f"Error requesting new identity: {e}")
        return False
    
    def check_connection(self) -> bool:
        """Check Tor connection"""
        if not self.is_running or not self.session:
            return False
        
        return self.session.check_tor_connection()
    
    def get_current_ip(self) -> Optional[str]:
        """Get current Tor IP address"""
        if not self.is_running or not self.session:
            return None
        
        return self.session.get_tor_ip()
    
    def get_circuit_info(self) -> Dict[str, Any]:
        """Get information about current circuits"""
        info = {
            'circuits': [],
            'streams': [],
            'exit_node': None
        }
        
        try:
            if self.controller:
                # Get circuits
                for circuit in self.controller.get_circuits():
                    circuit_info = {
                        'id': circuit.id,
                        'status': circuit.status,
                        'path': [(relay.fingerprint, relay.nickname) for relay in circuit.path],
                        'purpose': circuit.purpose,
                        'build_flags': circuit.build_flags
                    }
                    info['circuits'].append(circuit_info)
                
                # Get streams
                for stream in self.controller.get_streams():
                    stream_info = {
                        'id': stream.id,
                        'status': stream.status,
                        'target': stream.target,
                        'target_port': stream.target_port,
                        'circuit_id': stream.circ_id
                    }
                    info['streams'].append(stream_info)
                
                # Get exit node from first circuit
                circuits = self.controller.get_circuits()
                if circuits:
                    exit_relay = circuits[0].path[-1] if circuits[0].path else None
                    if exit_relay:
                        info['exit_node'] = {
                            'fingerprint': exit_relay.fingerprint,
                            'nickname': exit_relay.nickname
                        }
                        
        except Exception as e:
            print(f"Error getting circuit info: {e}")
        
        return info
    
    def is_tor_running(self) -> bool:
        """Check if Tor is running"""
        return self.is_running and check_tor_service('127.0.0.1', self.socks_port)
    
    def get_status(self) -> Dict[str, Any]:
        """Get Tor handler status"""
        status = {
            'is_running': self.is_tor_running(),
            'socks_port': self.socks_port,
            'control_port': self.control_port,
            'has_controller': self.controller is not None,
            'has_session': self.session is not None,
            'connection_ok': False,
            'current_ip': None
        }
        
        if status['is_running']:
            status['connection_ok'] = self.check_connection()
            status['current_ip'] = self.get_current_ip()
        
        return status


# Global Tor handler instance
_tor_handler = None


def get_tor_handler() -> TorHandler:
    """Get global Tor handler instance"""
    global _tor_handler
    if _tor_handler is None:
        _tor_handler = TorHandler()
    return _tor_handler