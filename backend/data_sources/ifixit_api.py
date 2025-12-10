"""
iFixit API Integration
Fetch repair guides, parts, and community solutions
"""

import requests
import json
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class IFixitAPI:
    """
    iFixit API client for repair guides and solutions
    Docs: https://www.ifixit.com/api/2.0/doc
    """
    
    BASE_URL = "https://www.ifixit.com/api/2.0"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AR-Laptop-Troubleshooter/1.0"
        })
    
    def search_device(self, query: str, device_type: str = "laptop") -> List[Dict]:
        """
        Search for device guides
        
        Args:
            query: Device model (e.g., "Lenovo IdeaPad 5")
            device_type: Type filter (laptop, tablet, etc.)
        
        Returns:
            List of device guides with URLs and metadata
        """
        try:
            url = f"{self.BASE_URL}/search/{query}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            # Filter for laptops
            laptop_results = [
                r for r in results 
                if r.get("type") == "device" and device_type.lower() in r.get("title", "").lower()
            ]
            
            return laptop_results
            
        except Exception as e:
            print(f"iFixit search error: {e}")
            return []
    
    def get_guide(self, guide_id: int) -> Optional[Dict]:
        """
        Get detailed repair guide
        
        Args:
            guide_id: iFixit guide ID
        
        Returns:
            Guide with steps, images, tools, parts
        """
        try:
            url = f"{self.BASE_URL}/guides/{guide_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            guide = response.json()
            
            # Extract structured data
            return {
                "id": guide.get("guideid"),
                "title": guide.get("title"),
                "device": guide.get("device"),
                "type": guide.get("type"),  # Installation, Disassembly, Repair
                "difficulty": guide.get("difficulty"),
                "time_required": guide.get("time_required"),
                "steps": self._parse_steps(guide.get("steps", [])),
                "tools": guide.get("tools", []),
                "parts": guide.get("parts", []),
                "conclusion": guide.get("conclusion"),
                "author": guide.get("author", {}).get("text"),
                "url": f"https://www.ifixit.com/Guide/{guide.get('url')}"
            }
            
        except Exception as e:
            print(f"iFixit guide fetch error: {e}")
            return None
    
    def _parse_steps(self, steps: List[Dict]) -> List[Dict]:
        """Parse guide steps into canonical format"""
        parsed = []
        
        for idx, step in enumerate(steps, 1):
            parsed.append({
                "step_number": idx,
                "title": step.get("title", f"Step {idx}"),
                "lines": [
                    {
                        "text": line.get("text"),
                        "level": line.get("level"),  # bullet, icon_note, icon_caution, icon_reminder
                    }
                    for line in step.get("lines", [])
                ],
                "images": [
                    {
                        "url": img.get("original"),
                        "thumbnail": img.get("medium"),
                        "id": img.get("id")
                    }
                    for img in step.get("media", {}).get("data", [])
                    if img.get("type") == "image"
                ],
                "videos": [
                    {
                        "url": vid.get("url"),
                        "thumbnail": vid.get("thumbnail")
                    }
                    for vid in step.get("media", {}).get("data", [])
                    if vid.get("type") == "video"
                ]
            })
        
        return parsed
    
    def get_device_info(self, device_name: str) -> Optional[Dict]:
        """
        Get device wiki info
        
        Args:
            device_name: Device name (e.g., "Lenovo_IdeaPad_5")
        
        Returns:
            Device info with specs, guides, parts
        """
        try:
            url = f"{self.BASE_URL}/wikis/CATEGORY/{device_name}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"iFixit device info error: {e}")
            return None
    
    def get_answers(self, device_name: str, problem: str) -> List[Dict]:
        """
        Get community answers for common problems
        
        Args:
            device_name: Device model
            problem: Issue description
        
        Returns:
            List of Q&A posts with solutions
        """
        try:
            # Search iFixit Answers
            search_query = f"{device_name} {problem}"
            url = f"{self.BASE_URL}/search/{search_query}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Filter for answers
            answers = [
                r for r in data.get("results", [])
                if r.get("type") == "answer"
            ]
            
            return answers
            
        except Exception as e:
            print(f"iFixit answers error: {e}")
            return []


# Example usage
if __name__ == "__main__":
    api = IFixitAPI()
    
    # Test search
    print("Searching for Lenovo IdeaPad 5...")
    results = api.search_device("Lenovo IdeaPad 5")
    print(f"Found {len(results)} results")
    
    if results:
        print(f"\nFirst result: {results[0].get('title')}")
    
    # Test guide fetch (example guide ID)
    print("\nFetching sample guide...")
    guide = api.get_guide(137177)  # Example: Lenovo battery replacement
    if guide:
        print(f"Guide: {guide['title']}")
        print(f"Steps: {len(guide['steps'])}")
        print(f"Tools: {guide['tools']}")
