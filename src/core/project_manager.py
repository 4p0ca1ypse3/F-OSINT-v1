"""
Project management for F-OSINT DWv1
"""

import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from utils.file_utils import get_data_dir, save_json, load_json


class Project:
    """OSINT Project model"""
    
    def __init__(self, project_id: str = None, name: str = "", description: str = "",
                 user_id: str = "", created_at: str = None, updated_at: str = None,
                 data: Dict[str, Any] = None, tags: List[str] = None):
        self.project_id = project_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.user_id = user_id
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.data = data or {
            'targets': [],
            'findings': [],
            'reports': [],
            'searches': [],
            'notes': []
        }
        self.tags = tags or []
    
    def add_target(self, target: Dict[str, Any]):
        """Add a target to the project"""
        target['id'] = str(uuid.uuid4())
        target['added_at'] = datetime.now().isoformat()
        self.data['targets'].append(target)
        self.updated_at = datetime.now().isoformat()
    
    def add_finding(self, finding: Dict[str, Any]):
        """Add a finding to the project"""
        finding['id'] = str(uuid.uuid4())
        finding['found_at'] = datetime.now().isoformat()
        self.data['findings'].append(finding)
        self.updated_at = datetime.now().isoformat()
    
    def add_search(self, search: Dict[str, Any]):
        """Add a search record to the project"""
        search['id'] = str(uuid.uuid4())
        search['performed_at'] = datetime.now().isoformat()
        self.data['searches'].append(search)
        self.updated_at = datetime.now().isoformat()
    
    def add_note(self, note: str, category: str = "general"):
        """Add a note to the project"""
        note_obj = {
            'id': str(uuid.uuid4()),
            'content': note,
            'category': category,
            'created_at': datetime.now().isoformat()
        }
        self.data['notes'].append(note_obj)
        self.updated_at = datetime.now().isoformat()
    
    def add_report(self, report_path: str, report_type: str):
        """Add a report to the project"""
        report = {
            'id': str(uuid.uuid4()),
            'path': report_path,
            'type': report_type,
            'generated_at': datetime.now().isoformat()
        }
        self.data['reports'].append(report)
        self.updated_at = datetime.now().isoformat()
    
    def get_finding_count(self) -> int:
        """Get number of findings"""
        return len(self.data.get('findings', []))
    
    def get_target_count(self) -> int:
        """Get number of targets"""
        return len(self.data.get('targets', []))
    
    def get_search_count(self) -> int:
        """Get number of searches"""
        return len(self.data.get('searches', []))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary"""
        return {
            'project_id': self.project_id,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'data': self.data,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create project from dictionary"""
        return cls(**data)


class ProjectManager:
    """Project management system"""
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id
        self.projects_dir = os.path.join(get_data_dir(), 'projects')
        self.current_project = None
        os.makedirs(self.projects_dir, exist_ok=True)
    
    def create_project(self, name: str, description: str = "", tags: List[str] = None) -> Project:
        """Create a new project"""
        project = Project(
            name=name,
            description=description,
            user_id=self.user_id or "anonymous",
            tags=tags or []
        )
        
        if self._save_project(project):
            self.current_project = project
            return project
        return None
    
    def load_project(self, project_id: str) -> Optional[Project]:
        """Load project by ID"""
        project_file = os.path.join(self.projects_dir, f"{project_id}.json")
        project_data = load_json(project_file)
        
        if project_data:
            project = Project.from_dict(project_data)
            self.current_project = project
            return project
        return None
    
    def save_current_project(self) -> bool:
        """Save current project"""
        if self.current_project:
            return self._save_project(self.current_project)
        return False
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        project_file = os.path.join(self.projects_dir, f"{project_id}.json")
        try:
            if os.path.exists(project_file):
                os.remove(project_file)
                if self.current_project and self.current_project.project_id == project_id:
                    self.current_project = None
                return True
        except Exception as e:
            print(f"Error deleting project {project_id}: {e}")
        return False
    
    def list_projects(self, user_id: str = None) -> List[Project]:
        """List all projects for a user"""
        target_user_id = user_id or self.user_id
        projects = []
        
        for filename in os.listdir(self.projects_dir):
            if filename.endswith('.json'):
                project_file = os.path.join(self.projects_dir, filename)
                project_data = load_json(project_file)
                
                if project_data:
                    project = Project.from_dict(project_data)
                    if not target_user_id or project.user_id == target_user_id:
                        projects.append(project)
        
        # Sort by updated_at (most recent first)
        projects.sort(key=lambda p: p.updated_at, reverse=True)
        return projects
    
    def search_projects(self, query: str, user_id: str = None) -> List[Project]:
        """Search projects by name, description, or tags"""
        projects = self.list_projects(user_id)
        query = query.lower()
        
        results = []
        for project in projects:
            if (query in project.name.lower() or 
                query in project.description.lower() or
                any(query in tag.lower() for tag in project.tags)):
                results.append(project)
        
        return results
    
    def get_project_summary(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project summary"""
        project = self.load_project(project_id)
        if not project:
            return None
        
        return {
            'project_id': project.project_id,
            'name': project.name,
            'description': project.description,
            'created_at': project.created_at,
            'updated_at': project.updated_at,
            'tags': project.tags,
            'stats': {
                'targets': project.get_target_count(),
                'findings': project.get_finding_count(),
                'searches': project.get_search_count(),
                'notes': len(project.data.get('notes', [])),
                'reports': len(project.data.get('reports', []))
            }
        }
    
    def export_project(self, project_id: str, export_path: str) -> bool:
        """Export project to file"""
        project = self.load_project(project_id)
        if project:
            return save_json(project.to_dict(), export_path)
        return False
    
    def import_project(self, import_path: str) -> Optional[Project]:
        """Import project from file"""
        project_data = load_json(import_path)
        if project_data:
            # Generate new project ID to avoid conflicts
            project_data['project_id'] = str(uuid.uuid4())
            project_data['user_id'] = self.user_id or "anonymous"
            project_data['imported_at'] = datetime.now().isoformat()
            
            project = Project.from_dict(project_data)
            if self._save_project(project):
                return project
        return None
    
    def _save_project(self, project: Project) -> bool:
        """Save project to file"""
        project_file = os.path.join(self.projects_dir, f"{project.project_id}.json")
        project.updated_at = datetime.now().isoformat()
        return save_json(project.to_dict(), project_file)
    
    def get_current_project(self) -> Optional[Project]:
        """Get current project"""
        return self.current_project
    
    def set_current_project(self, project_id: str) -> bool:
        """Set current project"""
        project = self.load_project(project_id)
        if project:
            self.current_project = project
            return True
        return False