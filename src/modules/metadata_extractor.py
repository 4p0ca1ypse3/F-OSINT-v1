"""
Metadata extractor module for F-OSINT DWv1
"""

import os
import mimetypes
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS

from utils.file_utils import get_temp_dir


@dataclass
class FileMetadata:
    """File metadata information"""
    filename: str
    file_size: int
    file_type: str
    mime_type: str
    created_date: str = ""
    modified_date: str = ""
    accessed_date: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MetadataExtractor:
    """Extract metadata from various file types"""
    
    def __init__(self):
        self.supported_types = {
            'image': ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif'],
            'document': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'media': ['.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac']
        }
    
    def extract_metadata(self, file_path: str) -> FileMetadata:
        """Extract metadata from file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Basic file information
        stat_info = os.stat(file_path)
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        
        metadata = FileMetadata(
            filename=filename,
            file_size=stat_info.st_size,
            file_type=self._get_file_type(file_ext),
            mime_type=mimetypes.guess_type(file_path)[0] or 'unknown',
            created_date=datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            modified_date=datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            accessed_date=datetime.fromtimestamp(stat_info.st_atime).isoformat()
        )
        
        # Extract type-specific metadata
        try:
            if metadata.file_type == 'image':
                metadata.metadata = self._extract_image_metadata(file_path)
            elif metadata.file_type == 'document':
                metadata.metadata = self._extract_document_metadata(file_path)
            elif metadata.file_type == 'media':
                metadata.metadata = self._extract_media_metadata(file_path)
            elif metadata.file_type == 'archive':
                metadata.metadata = self._extract_archive_metadata(file_path)
            else:
                metadata.metadata = self._extract_basic_metadata(file_path)
        except Exception as e:
            print(f"Error extracting metadata from {filename}: {e}")
            metadata.metadata = {'error': str(e)}
        
        return metadata
    
    def _get_file_type(self, file_ext: str) -> str:
        """Determine file type category"""
        for file_type, extensions in self.supported_types.items():
            if file_ext in extensions:
                return file_type
        return 'unknown'
    
    def _extract_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from image files"""
        metadata = {}
        
        try:
            with Image.open(file_path) as image:
                # Basic image info
                metadata['dimensions'] = f"{image.width}x{image.height}"
                metadata['format'] = image.format
                metadata['mode'] = image.mode
                
                # EXIF data
                exif_data = image._getexif()
                if exif_data:
                    exif = {}
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        
                        # Convert bytes to string if necessary
                        if isinstance(value, bytes):
                            try:
                                value = value.decode('utf-8')
                            except:
                                value = str(value)
                        
                        exif[tag] = value
                    
                    metadata['exif'] = exif
                    
                    # Extract important EXIF fields
                    if 'DateTime' in exif:
                        metadata['date_taken'] = exif['DateTime']
                    
                    if 'Make' in exif:
                        metadata['camera_make'] = exif['Make']
                    
                    if 'Model' in exif:
                        metadata['camera_model'] = exif['Model']
                    
                    if 'GPSInfo' in exif:
                        metadata['gps_info'] = self._extract_gps_info(exif['GPSInfo'])
                    
                    if 'Software' in exif:
                        metadata['software'] = exif['Software']
        
        except Exception as e:
            metadata['error'] = f"Failed to extract image metadata: {e}"
        
        return metadata
    
    def _extract_gps_info(self, gps_data: Dict) -> Dict[str, Any]:
        """Extract GPS information from EXIF data"""
        gps_info = {}
        
        try:
            if 1 in gps_data and 2 in gps_data and 3 in gps_data and 4 in gps_data:
                lat_ref = gps_data[1]
                lat = gps_data[2]
                lon_ref = gps_data[3]
                lon = gps_data[4]
                
                # Convert to decimal degrees
                lat_decimal = self._convert_to_degrees(lat)
                if lat_ref == 'S':
                    lat_decimal = -lat_decimal
                
                lon_decimal = self._convert_to_degrees(lon)
                if lon_ref == 'W':
                    lon_decimal = -lon_decimal
                
                gps_info['latitude'] = lat_decimal
                gps_info['longitude'] = lon_decimal
                gps_info['coordinates'] = f"{lat_decimal}, {lon_decimal}"
            
            if 5 in gps_data and 6 in gps_data:
                alt_ref = gps_data[5]
                alt = gps_data[6]
                altitude = float(alt)
                if alt_ref == 1:
                    altitude = -altitude
                gps_info['altitude'] = altitude
            
            if 7 in gps_data:
                gps_info['timestamp'] = gps_data[7]
            
            if 29 in gps_data:
                gps_info['date'] = gps_data[29]
        
        except Exception as e:
            gps_info['error'] = f"Failed to extract GPS info: {e}"
        
        return gps_info
    
    def _convert_to_degrees(self, value):
        """Convert GPS coordinates to decimal degrees"""
        d, m, s = value
        return float(d) + float(m)/60 + float(s)/3600
    
    def _extract_document_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from document files"""
        metadata = {}
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            metadata = self._extract_pdf_metadata(file_path)
        elif file_ext in ['.doc', '.docx']:
            metadata = self._extract_word_metadata(file_path)
        elif file_ext in ['.xls', '.xlsx']:
            metadata = self._extract_excel_metadata(file_path)
        else:
            metadata['note'] = 'Document metadata extraction not implemented for this format'
        
        return metadata
    
    def _extract_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF files"""
        metadata = {}
        
        try:
            # This would require PyPDF2 or similar library
            # For now, return placeholder
            metadata['note'] = 'PDF metadata extraction requires PyPDF2 library'
        except Exception as e:
            metadata['error'] = f"Failed to extract PDF metadata: {e}"
        
        return metadata
    
    def _extract_word_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from Word documents"""
        metadata = {}
        
        try:
            # This would require python-docx library
            # For now, return placeholder
            metadata['note'] = 'Word document metadata extraction requires python-docx library'
        except Exception as e:
            metadata['error'] = f"Failed to extract Word metadata: {e}"
        
        return metadata
    
    def _extract_excel_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from Excel files"""
        metadata = {}
        
        try:
            # This would require openpyxl library
            # For now, return placeholder
            metadata['note'] = 'Excel metadata extraction requires openpyxl library'
        except Exception as e:
            metadata['error'] = f"Failed to extract Excel metadata: {e}"
        
        return metadata
    
    def _extract_media_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from media files"""
        metadata = {}
        
        try:
            # This would require libraries like mutagen for audio, opencv for video
            # For now, return placeholder
            metadata['note'] = 'Media metadata extraction requires additional libraries'
        except Exception as e:
            metadata['error'] = f"Failed to extract media metadata: {e}"
        
        return metadata
    
    def _extract_archive_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from archive files"""
        metadata = {}
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.zip':
                metadata = self._extract_zip_metadata(file_path)
            else:
                metadata['note'] = f'Archive metadata extraction not implemented for {file_ext}'
        except Exception as e:
            metadata['error'] = f"Failed to extract archive metadata: {e}"
        
        return metadata
    
    def _extract_zip_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from ZIP files"""
        metadata = {}
        
        try:
            import zipfile
            
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                info_list = zip_file.infolist()
                
                metadata['file_count'] = len(info_list)
                metadata['total_uncompressed_size'] = sum(info.file_size for info in info_list)
                metadata['compression_ratio'] = sum(info.compress_size for info in info_list) / metadata['total_uncompressed_size'] if metadata['total_uncompressed_size'] > 0 else 0
                
                # File list (limited to first 20 files)
                metadata['files'] = []
                for info in info_list[:20]:
                    file_info = {
                        'filename': info.filename,
                        'file_size': info.file_size,
                        'compress_size': info.compress_size,
                        'date_time': f"{info.date_time[0]}-{info.date_time[1]:02d}-{info.date_time[2]:02d} {info.date_time[3]:02d}:{info.date_time[4]:02d}:{info.date_time[5]:02d}"
                    }
                    metadata['files'].append(file_info)
                
                if len(info_list) > 20:
                    metadata['note'] = f'Showing first 20 files out of {len(info_list)} total files'
        
        except Exception as e:
            metadata['error'] = f"Failed to extract ZIP metadata: {e}"
        
        return metadata
    
    def _extract_basic_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract basic metadata for unknown file types"""
        metadata = {}
        
        try:
            # File signature (magic bytes)
            with open(file_path, 'rb') as f:
                signature = f.read(16)
                metadata['file_signature'] = signature.hex()
                
                # Try to identify file type by signature
                file_type = self._identify_by_signature(signature)
                if file_type:
                    metadata['identified_type'] = file_type
            
            # Text content preview (for text files)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    preview = f.read(500)
                    if preview.strip():
                        metadata['text_preview'] = preview[:200] + '...' if len(preview) > 200 else preview
                        metadata['appears_to_be_text'] = True
            except:
                metadata['appears_to_be_text'] = False
        
        except Exception as e:
            metadata['error'] = f"Failed to extract basic metadata: {e}"
        
        return metadata
    
    def _identify_by_signature(self, signature: bytes) -> Optional[str]:
        """Identify file type by magic bytes"""
        signatures = {
            b'\x89PNG\r\n\x1a\n': 'PNG Image',
            b'\xff\xd8\xff': 'JPEG Image',
            b'GIF87a': 'GIF Image',
            b'GIF89a': 'GIF Image',
            b'%PDF': 'PDF Document',
            b'PK\x03\x04': 'ZIP Archive',
            b'Rar!': 'RAR Archive',
            b'\x7fELF': 'ELF Executable',
            b'MZ': 'Windows Executable',
        }
        
        for sig, file_type in signatures.items():
            if signature.startswith(sig):
                return file_type
        
        return None
    
    def analyze_privacy_risk(self, metadata: FileMetadata) -> Dict[str, Any]:
        """Analyze privacy risk of file metadata"""
        analysis = {
            'risk_level': 'low',
            'privacy_concerns': [],
            'sensitive_data_found': [],
            'recommendations': []
        }
        
        # Check for GPS coordinates
        if 'gps_info' in metadata.metadata:
            gps = metadata.metadata['gps_info']
            if 'coordinates' in gps:
                analysis['privacy_concerns'].append('GPS coordinates found')
                analysis['sensitive_data_found'].append(f"Location: {gps['coordinates']}")
                analysis['risk_level'] = 'high'
                analysis['recommendations'].append('Remove GPS data before sharing')
        
        # Check for camera information
        if 'camera_make' in metadata.metadata or 'camera_model' in metadata.metadata:
            analysis['privacy_concerns'].append('Camera information found')
            analysis['recommendations'].append('Consider removing camera metadata')
        
        # Check for software information
        if 'software' in metadata.metadata:
            analysis['privacy_concerns'].append('Software information found')
            analysis['sensitive_data_found'].append(f"Software: {metadata.metadata['software']}")
        
        # Check for creation dates
        if metadata.created_date:
            analysis['sensitive_data_found'].append(f"Created: {metadata.created_date}")
        
        # Overall risk assessment
        if len(analysis['privacy_concerns']) >= 3:
            analysis['risk_level'] = 'high'
        elif len(analysis['privacy_concerns']) >= 1:
            analysis['risk_level'] = 'medium'
        
        return analysis
    
    def remove_metadata(self, file_path: str, output_path: str = None) -> bool:
        """Remove metadata from file (basic implementation)"""
        if not output_path:
            output_path = file_path
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext in ['.jpg', '.jpeg']:
                return self._remove_image_metadata(file_path, output_path)
            else:
                print(f"Metadata removal not implemented for {file_ext} files")
                return False
        except Exception as e:
            print(f"Error removing metadata: {e}")
            return False
    
    def _remove_image_metadata(self, file_path: str, output_path: str) -> bool:
        """Remove metadata from image files"""
        try:
            with Image.open(file_path) as image:
                # Create new image without EXIF data
                data = list(image.getdata())
                clean_image = Image.new(image.mode, image.size)
                clean_image.putdata(data)
                clean_image.save(output_path)
            return True
        except Exception as e:
            print(f"Error removing image metadata: {e}")
            return False
    
    def export_metadata(self, metadata: FileMetadata, format_type: str = 'json') -> str:
        """Export metadata in specified format"""
        if format_type == 'json':
            import json
            return json.dumps({
                'filename': metadata.filename,
                'file_size': metadata.file_size,
                'file_type': metadata.file_type,
                'mime_type': metadata.mime_type,
                'created_date': metadata.created_date,
                'modified_date': metadata.modified_date,
                'accessed_date': metadata.accessed_date,
                'metadata': metadata.metadata
            }, indent=2)
        
        elif format_type == 'text':
            output = []
            output.append(f"File: {metadata.filename}")
            output.append(f"Size: {metadata.file_size} bytes")
            output.append(f"Type: {metadata.file_type}")
            output.append(f"MIME Type: {metadata.mime_type}")
            output.append(f"Created: {metadata.created_date}")
            output.append(f"Modified: {metadata.modified_date}")
            output.append(f"Accessed: {metadata.accessed_date}")
            output.append("\nMetadata:")
            
            for key, value in metadata.metadata.items():
                output.append(f"  {key}: {value}")
            
            return '\n'.join(output)
        
        return ""