#!/usr/bin/env python3
"""
SharePoint Folder Scanner using Microsoft Graph API
Uses interactive browser authentication (MSAL)
No credentials needed in code - secure OAuth flow
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import urllib.parse

try:
    from msal import PublicClientApplication
    import requests
except ImportError:
    print("❌ Required packages not installed!")
    print("\nPlease install dependencies:")
    print("  pip install msal requests")
    sys.exit(1)

try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False

try:
    from openpyxl import load_workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


class SharePointScanner:
    """Microsoft Graph API client for SharePoint access"""
    
    # Microsoft Graph API endpoints
    AUTHORITY = "https://login.microsoftonline.com/common"
    GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"
    
    # OVES custom Azure AD application client ID
    CLIENT_ID = "1df26ef8-c7ce-4aee-aff2-bc36342362e0"
    
    # Required permissions
    SCOPES = [
        "Files.Read.All",
        "Sites.Read.All",
        "User.Read"
    ]
    
    def __init__(self, cache_file: str = ".sharepoint_token_cache.json", workspace_root: Optional[Path] = None):
        """Initialize with token caching"""
        # Use script directory for cache file
        script_dir = Path(__file__).parent.parent  # Go up to tools/sharepoint/
        self.cache_file = script_dir / cache_file
        self.token_cache = self._load_cache()
        self.app = PublicClientApplication(
            self.CLIENT_ID,
            authority=self.AUTHORITY,
            token_cache=self.token_cache
        )
        self.access_token = None
        # Set workspace root
        if workspace_root:
            self.workspace_root = workspace_root
        else:
            self.workspace_root = Path(__file__).parent.parent.parent  # Up to github/
        
    def _load_cache(self):
        """Load token cache from file"""
        from msal import SerializableTokenCache
        cache = SerializableTokenCache()
        if self.cache_file.exists():
            cache.deserialize(self.cache_file.read_text())
        return cache
    
    def _save_cache(self):
        """Save token cache to file"""
        if self.token_cache.has_state_changed:
            self.cache_file.write_text(self.token_cache.serialize())
            print(f"✓ Token cached to: {self.cache_file}")
    
    def authenticate(self):
        """Authenticate using interactive browser flow"""
        print("\n" + "="*60)
        print("Microsoft Authentication Required")
        print("="*60)
        
        # Try to get token from cache first
        accounts = self.app.get_accounts()
        if accounts:
            print(f"\n✓ Found cached account: {accounts[0]['username']}")
            result = self.app.acquire_token_silent(self.SCOPES, account=accounts[0])
            if result and "access_token" in result:
                self.access_token = result["access_token"]
                print("✓ Using cached token")
                return True
        
        # Interactive login required
        print("\n🔐 Opening browser for authentication...")
        print("Please log in with your Microsoft 365 credentials")
        
        result = self.app.acquire_token_interactive(
            scopes=self.SCOPES,
            prompt="select_account"
        )
        
        if "access_token" in result:
            self.access_token = result["access_token"]
            self._save_cache()
            print("\n✓ Authentication successful!")
            return True
        else:
            error = result.get("error_description", result.get("error"))
            print(f"\n❌ Authentication failed: {error}")
            return False
    
    def _make_request(self, endpoint: str, method: str = "GET") -> Optional[Dict]:
        """Make authenticated request to Graph API"""
        if not self.access_token:
            print("❌ Not authenticated. Call authenticate() first.")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }
        
        url = f"{self.GRAPH_ENDPOINT}{endpoint}"
        
        try:
            response = requests.request(method, url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"❌ API Error: {e}")
            print(f"Response: {response.text}")
            return None
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def resolve_sharing_link(self, sharing_url: str) -> Optional[Dict]:
        """Resolve a SharePoint sharing link to a drive item"""
        # Use the sharing URL directly with unpadded base64 encoding
        base64_url = self._base64_encode(sharing_url)
        
        # Use shares endpoint to resolve the link
        endpoint = f"/shares/u!{base64_url}/driveItem"
        return self._make_request(endpoint)
    
    def _base64_encode(self, text: str) -> str:
        """Base64 encode for URL (unpadded, URL-safe)"""
        import base64
        encoded = base64.urlsafe_b64encode(text.encode()).decode()
        return encoded.rstrip('=')
    
    def list_folder_contents(self, drive_id: str, item_id: str) -> List[Dict]:
        """List contents of a folder"""
        endpoint = f"/drives/{drive_id}/items/{item_id}/children"
        result = self._make_request(endpoint)
        
        if result and "value" in result:
            return result["value"]
        return []
    
    def get_folder_by_path(self, site_id: str, folder_path: str) -> Optional[Dict]:
        """Get folder item by path"""
        # Encode path
        encoded_path = urllib.parse.quote(folder_path)
        endpoint = f"/sites/{site_id}/drive/root:/{encoded_path}"
        return self._make_request(endpoint)
    
    def list_my_sites(self) -> List[Dict]:
        """List all SharePoint sites user has access to"""
        endpoint = "/sites?search=*"
        result = self._make_request(endpoint)
        
        if result and "value" in result:
            return result["value"]
        return []
    
    def download_file(self, drive_id: str, item_id: str, output_path: str) -> bool:
        """Download a file from SharePoint"""
        endpoint = f"/drives/{drive_id}/items/{item_id}/content"
        url = f"{self.GRAPH_ENDPOINT}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }
        
        try:
            print(f"⏳ Downloading file...")
            response = requests.get(url, headers=headers, stream=True, timeout=120)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\r   Progress: {progress:.1f}% ({downloaded / 1024 / 1024:.2f} MB / {total_size / 1024 / 1024:.2f} MB)", end='', flush=True)
            
            print(f"\n✓ Downloaded successfully")
            return True
        except requests.exceptions.Timeout:
            print(f"\n❌ Download timeout (file too large or network slow)")
            return False
        except Exception as e:
            print(f"\n❌ Download failed: {e}")
            return False
    
    def analyze_powerpoint(self, pptx_path: str) -> Dict:
        """Analyze PowerPoint content and extract metadata"""
        if not PPTX_AVAILABLE:
            return {
                "error": "python-pptx not installed",
                "install": "pip install python-pptx"
            }
        
        try:
            print(f"\n⏳ Analyzing PowerPoint content...")
            prs = Presentation(pptx_path)
            
            slides_data = []
            total_images = 0
            total_shapes = 0
            
            for idx, slide in enumerate(prs.slides, 1):
                slide_info = {
                    "slide_number": idx,
                    "layout": slide.slide_layout.name if hasattr(slide.slide_layout, 'name') else "Unknown",
                    "shapes_count": len(slide.shapes),
                    "text_content": [],
                    "images": [],
                    "notes": ""
                }
                
                # Extract text from shapes
                for shape in slide.shapes:
                    total_shapes += 1
                    
                    # Text content
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_info["text_content"].append(shape.text.strip())
                    
                    # Images
                    if hasattr(shape, "image"):
                        total_images += 1
                        slide_info["images"].append({
                            "type": "image",
                            "format": shape.image.content_type if hasattr(shape.image, 'content_type') else "unknown"
                        })
                
                # Extract notes
                if slide.has_notes_slide:
                    notes_frame = slide.notes_slide.notes_text_frame
                    if notes_frame and notes_frame.text.strip():
                        slide_info["notes"] = notes_frame.text.strip()
                
                slides_data.append(slide_info)
            
            analysis = {
                "total_slides": len(prs.slides),
                "total_images": total_images,
                "total_shapes": total_shapes,
                "slide_size": {
                    "width": prs.slide_width,
                    "height": prs.slide_height
                },
                "slides": slides_data
            }
            
            print(f"✓ Analysis complete: {len(prs.slides)} slides, {total_images} images")
            return analysis
            
        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}"
            }
    
    def analyze_excel(self, xlsx_path: str) -> Dict:
        """Analyze Excel content and extract terms"""
        if not OPENPYXL_AVAILABLE:
            return {
                "error": "openpyxl not installed",
                "install": "pip install openpyxl"
            }
        
        try:
            print(f"\n⏳ Analyzing Excel content...")
            wb = load_workbook(xlsx_path, read_only=True, data_only=True)
            
            all_text = []
            sheet_data = []
            
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                sheet_text = []
                
                for row in sheet.iter_rows(values_only=True):
                    for cell in row:
                        if cell and isinstance(cell, str) and cell.strip():
                            sheet_text.append(cell.strip())
                            all_text.append(cell.strip())
                
                sheet_data.append({
                    "name": sheet_name,
                    "text_count": len(sheet_text)
                })
            
            # Extract unique terms (simple approach)
            terms = set()
            for text in all_text:
                # Split by common separators
                words = text.replace('、', ' ').replace('，', ' ').replace(',', ' ').split()
                for word in words:
                    if len(word) > 1:  # Filter out single characters
                        terms.add(word)
            
            analysis = {
                "total_sheets": len(wb.sheetnames),
                "total_text_cells": len(all_text),
                "unique_terms_count": len(terms),
                "terms": sorted(list(terms))[:100],  # First 100 terms
                "sheets": sheet_data
            }
            
            print(f"✓ Analysis complete: {len(wb.sheetnames)} sheets, {len(all_text)} text cells, {len(terms)} unique terms")
            return analysis
            
        except Exception as e:
            return {
                "error": f"Analysis failed: {str(e)}"
            }
    
    def analyze_file(self, sharing_url: str, output_file: Optional[str] = None) -> Dict:
        """
        Analyze a SharePoint file (PowerPoint, etc.)
        Downloads to session folder, keeps for re-analysis
        
        Args:
            sharing_url: SharePoint sharing link
            output_file: Optional path to save analysis JSON
            
        Returns:
            Dictionary with file analysis
        """
        print("\n" + "="*60)
        print("SharePoint File Analyzer")
        print("="*60)
        print(f"\n📄 Analyzing: {sharing_url}")
        
        # Resolve the sharing link
        print("\n⏳ Resolving sharing link...")
        file_item = self.resolve_sharing_link(sharing_url)
        
        if not file_item:
            print("❌ Could not resolve sharing link")
            return {}
        
        file_name = file_item.get('name', 'Unknown')
        file_size = file_item.get('size', 0)
        print(f"✓ Resolved: {file_name} ({file_size / 1024 / 1024:.2f} MB)")
        
        # Get drive and item IDs
        drive_id = file_item.get("parentReference", {}).get("driveId")
        item_id = file_item.get("id")
        
        if not drive_id or not item_id:
            print("❌ Could not get drive/item IDs")
            return {}
        
        # Determine file type
        file_ext = Path(file_name).suffix.lower()
        
        # Create session directory (workspace-root level)
        session_dir = self.workspace_root / ".sharepoint-session"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Download to session folder
        session_file = session_dir / file_name
        
        # Check if file already exists in session
        if session_file.exists():
            print(f"✓ Using cached file from session: {session_file.name}")
        else:
            # Download file
            if not self.download_file(drive_id, item_id, str(session_file)):
                return {}
            print(f"✓ File saved to session: {session_file}")
        
        # Analyze based on file type
        analysis = {}
        if file_ext == '.pptx':
            analysis = self.analyze_powerpoint(str(session_file))
        elif file_ext == '.xlsx':
            analysis = self.analyze_excel(str(session_file))
        else:
            analysis = {
                "message": f"File type {file_ext} analysis not yet implemented",
                "supported_types": [".pptx", ".xlsx"]
            }
        
        # Build results
        results = {
            "file_name": file_name,
            "file_url": sharing_url,
            "file_size": file_size,
            "file_type": file_ext,
            "scan_date": datetime.now().isoformat(),
            "session_file": str(session_file),
            "analysis": analysis
        }
        
        # Display results
        self._display_file_analysis(results)
        
        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.write_text(json.dumps(results, indent=2))
            print(f"\n✓ Analysis saved to: {output_path}")
        
        print(f"\n💾 File retained in session for re-analysis")
        
        return results
    
    def _display_file_analysis(self, results: Dict):
        """Display file analysis results in console"""
        print("\n" + "="*60)
        print("Analysis Results")
        print("="*60)
        print(f"\n📄 File: {results['file_name']}")
        print(f"📊 Size: {results['file_size'] / 1024 / 1024:.2f} MB")
        print(f"🔤 Type: {results['file_type']}")
        
        analysis = results.get('analysis', {})
        
        if 'error' in analysis:
            print(f"\n❌ Error: {analysis['error']}")
            if 'install' in analysis:
                print(f"   Install: {analysis['install']}")
            return
        
        if 'total_slides' in analysis:
            print(f"\n📑 PowerPoint Analysis:")
            print(f"   - Total Slides: {analysis['total_slides']}")
            print(f"   - Total Images: {analysis['total_images']}")
            print(f"   - Total Shapes: {analysis['total_shapes']}")
            print(f"   - Slide Dimensions: {analysis['slide_size']['width']}x{analysis['slide_size']['height']}")
            
            print(f"\n📋 Slide Contents:")
            print("-" * 60)
            for slide in analysis['slides'][:5]:  # Show first 5 slides
                print(f"\nSlide {slide['slide_number']} ({slide['layout']})")
                if slide['text_content']:
                    for text in slide['text_content'][:3]:  # First 3 text items
                        preview = text[:60] + "..." if len(text) > 60 else text
                        print(f"  • {preview}")
                if slide['images']:
                    print(f"  🖼️  {len(slide['images'])} image(s)")
            
            if analysis['total_slides'] > 5:
                print(f"\n... and {analysis['total_slides'] - 5} more slides")
            print("-" * 60)
    
    def scan_folder_recursive(self, drive_id: str, item_id: str, folder_name: str, depth: int = 0, max_depth: int = 10) -> Dict:
        """
        Recursively scan a folder and all its subfolders
        
        Args:
            drive_id: SharePoint drive ID
            item_id: Folder item ID
            folder_name: Name of the folder
            depth: Current recursion depth
            max_depth: Maximum recursion depth
            
        Returns:
            Dictionary with folder tree structure
        """
        if depth >= max_depth:
            return {"name": folder_name, "type": "folder", "items": [], "truncated": True}
        
        indent = "  " * depth
        print(f"{indent}📁 Scanning: {folder_name}")
        
        items = self.list_folder_contents(drive_id, item_id)
        
        result = {
            "name": folder_name,
            "type": "folder",
            "item_count": len(items),
            "items": []
        }
        
        for item in items:
            item_info = {
                "name": item.get("name"),
                "type": "folder" if "folder" in item else "file",
                "size": item.get("size", 0),
                "modified": item.get("lastModifiedDateTime"),
                "web_url": item.get("webUrl")
            }
            
            # If it's a folder, recurse into it
            if "folder" in item:
                sub_id = item.get("id")
                if sub_id:
                    sub_result = self.scan_folder_recursive(
                        drive_id, sub_id, item.get("name"), depth + 1, max_depth
                    )
                    item_info["items"] = sub_result.get("items", [])
                    item_info["item_count"] = sub_result.get("item_count", 0)
            
            result["items"].append(item_info)
        
        return result
    
    def scan_folder(self, sharing_url: str, output_file: Optional[str] = None, recursive: bool = False, max_depth: int = 10, filter_indices: Optional[List[int]] = None) -> Dict:
        """
        Scan a SharePoint folder from sharing link
        
        Args:
            sharing_url: SharePoint sharing link
            output_file: Optional path to save JSON output
            recursive: If True, scan all subfolders recursively
            max_depth: Maximum recursion depth for recursive scan
            
        Returns:
            Dictionary with folder contents and metadata
        """
        print("\n" + "="*60)
        print("SharePoint Folder Scanner" + (" (Recursive)" if recursive else ""))
        print("="*60)
        print(f"\n📁 Scanning: {sharing_url}")
        
        # Resolve the sharing link
        print("\n⏳ Resolving sharing link...")
        folder_item = self.resolve_sharing_link(sharing_url)
        
        if not folder_item:
            print("❌ Could not resolve sharing link")
            return {}
        
        print(f"✓ Resolved: {folder_item.get('name', 'Unknown')}")
        
        # Get folder contents
        drive_id = folder_item.get("parentReference", {}).get("driveId")
        item_id = folder_item.get("id")
        
        if not drive_id or not item_id:
            print("❌ Could not get drive/item IDs")
            return {}
        
        if recursive:
            print(f"\n⏳ Recursively scanning folder tree (max depth: {max_depth})...")
            folder_tree = self.scan_folder_recursive(drive_id, item_id, folder_item.get('name'), 0, max_depth)
            
            results = {
                "folder_name": folder_item.get("name"),
                "folder_url": sharing_url,
                "scan_date": datetime.now().isoformat(),
                "recursive": True,
                "max_depth": max_depth,
                "tree": folder_tree
            }
            
            # Display recursive results
            self._display_tree(folder_tree)
            
            # Save to file if requested
            if output_file:
                output_path = Path(output_file)
                output_path.write_text(json.dumps(results, indent=2))
                print(f"\n✓ Results saved to: {output_path}")
            
            return results
            
        else:
            print(f"\n⏳ Fetching folder contents...")
            items = self.list_folder_contents(drive_id, item_id)
            
            print(f"✓ Found {len(items)} items")
        
        # Build results
        results = {
            "folder_name": folder_item.get("name"),
            "folder_url": sharing_url,
            "scan_date": datetime.now().isoformat(),
            "item_count": len(items),
            "items": []
        }
        
        # Process items
        for item in items:
            item_info = {
                "name": item.get("name"),
                "type": "folder" if "folder" in item else "file",
                "size": item.get("size", 0),
                "modified": item.get("lastModifiedDateTime"),
                "created": item.get("createdDateTime"),
                "web_url": item.get("webUrl")
            }
            
            # Add file-specific info
            if "file" in item:
                item_info["mime_type"] = item["file"].get("mimeType")
                if "image" in item:
                    item_info["dimensions"] = {
                        "width": item["image"].get("width"),
                        "height": item["image"].get("height")
                    }
            
            results["items"].append(item_info)
        
        # Apply filter if specified
        if filter_indices:
            filtered_items = []
            for idx in filter_indices:
                if 1 <= idx <= len(results["items"]):
                    filtered_items.append(results["items"][idx - 1])
            results["items"] = filtered_items
            results["item_count"] = len(filtered_items)
            results["filtered"] = True
            results["filter_indices"] = filter_indices
        
        # Display results
        self._display_results(results)
        
        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.write_text(json.dumps(results, indent=2))
            print(f"\n✓ Results saved to: {output_path}")
        
        return results
    
    def _display_tree(self, tree: Dict, depth: int = 0):
        """Display folder tree in console"""
        print("\n" + "="*60)
        print("Recursive Scan Results")
        print("="*60)
        
        def print_tree(node: Dict, indent: str = "", is_last: bool = True):
            # Print current node
            connector = "└── " if is_last else "├── "
            icon = "📁" if node['type'] == 'folder' else "📄"
            size_str = f" ({node['size'] / 1024:.1f} KB)" if node.get('size', 0) > 0 else ""
            item_count = f" [{node.get('item_count', 0)} items]" if node['type'] == 'folder' and 'item_count' in node else ""
            print(f"{indent}{connector}{icon} {node['name']}{size_str}{item_count}")
            
            # Print children
            if 'items' in node and node['items']:
                extension = "    " if is_last else "│   "
                for i, child in enumerate(node['items']):
                    is_last_child = (i == len(node['items']) - 1)
                    print_tree(child, indent + extension, is_last_child)
        
        print_tree(tree)
        print("-" * 60)
    
    def _display_results(self, results: Dict):
        """Display scan results in console"""
        print("\n" + "="*60)
        print("Scan Results")
        print("="*60)
        print(f"\n📁 Folder: {results['folder_name']}")
        print(f"📊 Total Items: {results['item_count']}")
        
        # Count by type
        files = [i for i in results['items'] if i['type'] == 'file']
        folders = [i for i in results['items'] if i['type'] == 'folder']
        
        print(f"   - Files: {len(files)}")
        print(f"   - Folders: {len(folders)}")
        
        # List items
        print("\n📋 Contents:")
        print("-" * 60)
        
        for item in results['items']:
            icon = "📁" if item['type'] == 'folder' else "📄"
            size_str = f"{item['size'] / 1024:.1f} KB" if item['size'] > 0 else ""
            print(f"{icon} {item['name']:<40} {size_str:>10}")
        
        print("-" * 60)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Scan SharePoint folders using Microsoft Graph API"
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="SharePoint sharing URL to scan"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output JSON file path",
        default=None
    )
    parser.add_argument(
        "--list-sites",
        action="store_true",
        help="List all accessible SharePoint sites"
    )
    parser.add_argument(
        "--analyze-file",
        action="store_true",
        help="Analyze file content (PowerPoint, etc.)"
    )
    parser.add_argument(
        "--cleanup-session",
        action="store_true",
        help="Delete all files in session temp folder"
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively scan all subfolders"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="Maximum recursion depth (default: 10)"
    )
    parser.add_argument(
        "--filter",
        help="Comma-separated list of file indices to filter (e.g., '1,4,5,6')",
        default=None
    )
    parser.add_argument(
        "--download-analyze",
        action="store_true",
        help="Download and analyze filtered files (Excel/PowerPoint)"
    )
    
    args = parser.parse_args()
    
    # Initialize scanner
    scanner = SharePointScanner()
    
    # Cleanup session mode
    if args.cleanup_session:
        import shutil
        # Use workspace root for session directory
        workspace_root = Path(__file__).parent.parent.parent  # Up to github/
        session_dir = workspace_root / ".sharepoint-session"
        
        if not session_dir.exists():
            print("✓ Session folder is empty (doesn't exist)")
            return
        
        # List files before cleanup
        files = list(session_dir.glob("*"))
        if not files:
            print("✓ Session folder is empty")
            return
        
        print(f"\n🗑️  Found {len(files)} file(s) in session:")
        total_size = 0
        for f in files:
            if f.is_file():
                size = f.stat().st_size
                total_size += size
                print(f"   • {f.name} ({size / 1024 / 1024:.2f} MB)")
        
        print(f"\nTotal size: {total_size / 1024 / 1024:.2f} MB")
        
        # Confirm deletion
        confirm = input("\nDelete all session files? (yes/no): ")
        if confirm.lower() in ['yes', 'y']:
            shutil.rmtree(session_dir)
            print("✓ Session folder cleaned up")
        else:
            print("Cleanup cancelled")
        return
    
    # Authenticate
    if not scanner.authenticate():
        sys.exit(1)
    
    # List sites mode
    if args.list_sites:
        print("\n📋 Fetching accessible SharePoint sites...")
        sites = scanner.list_my_sites()
        print(f"\n✓ Found {len(sites)} sites:\n")
        for site in sites[:10]:  # Show first 10
            print(f"  • {site.get('displayName')} - {site.get('webUrl')}")
        return
    
    # Analyze file mode
    if args.analyze_file:
        if not args.url:
            print("❌ Error: Please provide a SharePoint file URL")
            sys.exit(1)
        scanner.analyze_file(args.url, args.output)
        return
    
    # Scan folder mode (default)
    if not args.url:
        print("❌ Error: Please provide a SharePoint sharing URL")
        print("\nUsage:")
        print("  python scan-sharepoint-graph.py <SHAREPOINT_URL>")
        print("\nExamples:")
        print("  # Scan folder:")
        print("  python scan-sharepoint-graph.py 'https://company.sharepoint.com/:f:/s/...'")
        print("\n  # Analyze PowerPoint file:")
        print("  python scan-sharepoint-graph.py 'https://company.sharepoint.com/:p:/s/...' --analyze-file")
        sys.exit(1)
    
    # Parse filter indices if provided
    filter_indices = None
    if args.filter:
        try:
            filter_indices = [int(i.strip()) for i in args.filter.split(',')]
            print(f"\n🔍 Filtering files: {filter_indices}")
        except ValueError:
            print("❌ Error: Invalid filter format. Use comma-separated numbers (e.g., '1,4,5,6')")
            sys.exit(1)
    
    # Scan the folder
    results = scanner.scan_folder(args.url, args.output, recursive=args.recursive, max_depth=args.max_depth, filter_indices=filter_indices)
    
    # Download and analyze filtered files if requested
    if args.download_analyze and filter_indices and results.get('items'):
        print("\n" + "="*60)
        print("Downloading and Analyzing Files")
        print("="*60)
        
        # Get drive_id from first item
        folder_item = scanner.resolve_sharing_link(args.url)
        if folder_item:
            drive_id = folder_item.get("parentReference", {}).get("driveId")
            item_id = folder_item.get("id")
            
            if drive_id and item_id:
                # Get all items again for download
                all_items = scanner.list_folder_contents(drive_id, item_id)
                
                # Create session directory
                session_dir = scanner.workspace_root / ".sharepoint-session"
                session_dir.mkdir(parents=True, exist_ok=True)
                
                analysis_results = []
                
                for idx in filter_indices:
                    if 1 <= idx <= len(all_items):
                        item = all_items[idx - 1]
                        file_name = item.get('name')
                        file_id = item.get('id')
                        file_size = item.get('size', 0)
                        
                        print(f"\n[{idx}] {file_name} ({file_size / 1024 / 1024:.2f} MB)")
                        
                        # Download file
                        session_file = session_dir / file_name
                        if session_file.exists():
                            print(f"✓ Using cached file")
                        else:
                            if scanner.download_file(drive_id, file_id, str(session_file)):
                                print(f"✓ Downloaded successfully")
                            else:
                                print(f"❌ Download failed")
                                continue
                        
                        # Analyze file
                        file_ext = Path(file_name).suffix.lower()
                        if file_ext == '.xlsx':
                            analysis = scanner.analyze_excel(str(session_file))
                            analysis_results.append({
                                "file_name": file_name,
                                "index": idx,
                                "analysis": analysis
                            })
                        elif file_ext == '.pptx':
                            analysis = scanner.analyze_powerpoint(str(session_file))
                            analysis_results.append({
                                "file_name": file_name,
                                "index": idx,
                                "analysis": analysis
                            })
                
                # Save combined analysis
                if args.output and analysis_results:
                    output_path = Path(args.output)
                    combined_results = {
                        "scan_date": datetime.now().isoformat(),
                        "folder_url": args.url,
                        "filtered_indices": filter_indices,
                        "files": analysis_results
                    }
                    output_path.write_text(json.dumps(combined_results, indent=2, ensure_ascii=False))
                    print(f"\n✓ Analysis results saved to: {output_path}")


if __name__ == "__main__":
    main()
