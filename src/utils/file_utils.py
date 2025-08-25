"""
File utilities for F-OSINT DWv1
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path


def ensure_directories():
    """Ensure all required directories exist"""
    base_dir = get_base_dir()
    dirs = [
        'data',
        'sessions',
        'reports',
        'temp',
        'data/users',
        'data/projects'
    ]
    
    for dir_name in dirs:
        dir_path = os.path.join(base_dir, dir_name)
        os.makedirs(dir_path, exist_ok=True)


def get_base_dir():
    """Get the base directory of the application"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_dir():
    """Get the data directory"""
    return os.path.join(get_base_dir(), 'data')


def get_reports_dir():
    """Get the reports directory"""
    return os.path.join(get_base_dir(), 'reports')


def get_sessions_dir():
    """Get the sessions directory"""
    return os.path.join(get_base_dir(), 'sessions')


def get_temp_dir():
    """Get the temporary directory"""
    return os.path.join(get_base_dir(), 'temp')


def save_json(data, filepath):
    """Save data to JSON file"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON to {filepath}: {e}")
        return False


def load_json(filepath):
    """Load data from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON from {filepath}: {e}")
        return None


def generate_filename(prefix, extension, timestamp=True):
    """Generate a filename with optional timestamp"""
    if timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{ts}.{extension}"
    return f"{prefix}.{extension}"


def safe_delete_file(filepath):
    """Safely delete a file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        return True
    except Exception as e:
        print(f"Error deleting file {filepath}: {e}")
        return False


def clean_temp_directory():
    """Clean temporary directory"""
    temp_dir = get_temp_dir()
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            os.makedirs(temp_dir, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error cleaning temp directory: {e}")
        return False


def get_file_size(filepath):
    """Get file size in bytes"""
    try:
        return os.path.getsize(filepath)
    except:
        return 0


def create_backup(filepath):
    """Create a backup of a file"""
    try:
        if os.path.exists(filepath):
            backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(filepath, backup_path)
            return backup_path
    except Exception as e:
        print(f"Error creating backup: {e}")
    return None