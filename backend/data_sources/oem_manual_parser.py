"""
OEM Manual PDF Parser
Extract repair procedures from service manuals
"""

import os
import re
from typing import List, Dict, Optional
from pathlib import Path
import fitz  # PyMuPDF

class OEMManualParser:
    """
    Parse OEM service manuals (PDFs) to extract repair procedures
    """
    
    def __init__(self, manuals_path: str = "../manuals"):
        self.manuals_path = Path(manuals_path)
    
    def get_brand_manuals(self, brand: str) -> List[Path]:
        """
        Get all PDF manuals for a brand
        
        Args:
            brand: Brand name (lenovo, dell, hp, etc.)
        
        Returns:
            List of PDF file paths
        """
        brand_dir = self.manuals_path / brand.lower()
        
        if not brand_dir.exists():
            return []
        
        return list(brand_dir.glob("*.pdf"))
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Dict[int, str]:
        """
        Extract text from PDF by page
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dictionary of {page_number: text_content}
        """
        pages = {}
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                pages[page_num + 1] = text
            
            doc.close()
            
        except Exception as e:
            print(f"PDF extraction error ({pdf_path.name}): {e}")
        
        return pages
    
    def find_repair_procedures(self, pdf_path: Path, component: str) -> List[Dict]:
        """
        Find repair procedures for specific component
        
        Args:
            pdf_path: Path to PDF manual
            component: Component name (battery, keyboard, fan, etc.)
        
        Returns:
            List of procedures with steps and page references
        """
        pages = self.extract_text_from_pdf(pdf_path)
        procedures = []
        
        # Search for component mentions
        component_lower = component.lower()
        
        for page_num, text in pages.items():
            text_lower = text.lower()
            
            # Check if this page discusses the component
            if component_lower in text_lower:
                # Look for removal/installation procedures
                if any(keyword in text_lower for keyword in [
                    "removal", "install", "replace", "disassembly", "assembly"
                ]):
                    # Extract procedure steps
                    steps = self._extract_steps_from_text(text)
                    
                    if steps:
                        procedures.append({
                            "pdf_name": pdf_path.name,
                            "page": page_num,
                            "component": component,
                            "steps": steps,
                            "text_excerpt": text[:500]  # First 500 chars
                        })
        
        return procedures
    
    def _extract_steps_from_text(self, text: str) -> List[str]:
        """
        Extract numbered steps from text
        
        Args:
            text: Raw text from PDF page
        
        Returns:
            List of step strings
        """
        steps = []
        
        # Pattern 1: "1. Step description"
        pattern1 = re.findall(r'^\s*(\d+)\.\s+(.+?)(?=\n\s*\d+\.|$)', text, re.MULTILINE | re.DOTALL)
        if pattern1:
            steps = [step[1].strip() for step in pattern1]
            return steps
        
        # Pattern 2: "Step 1: Description"
        pattern2 = re.findall(r'Step\s+(\d+):\s*(.+?)(?=Step\s+\d+:|$)', text, re.IGNORECASE | re.DOTALL)
        if pattern2:
            steps = [step[1].strip() for step in pattern2]
            return steps
        
        # Pattern 3: Bullet points
        pattern3 = re.findall(r'^\s*[•\-]\s+(.+?)$', text, re.MULTILINE)
        if pattern3:
            steps = [step.strip() for step in pattern3]
        
        return steps
    
    def extract_images_from_pdf(self, pdf_path: Path, output_dir: Path) -> List[Dict]:
        """
        Extract images from PDF for AR overlays
        
        Args:
            pdf_path: Path to PDF manual
            output_dir: Directory to save extracted images
        
        Returns:
            List of extracted image metadata
        """
        images = []
        
        try:
            doc = fitz.open(pdf_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Save image
                    image_filename = f"page{page_num+1}_img{img_index+1}.{image_ext}"
                    image_path = output_dir / image_filename
                    
                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)
                    
                    images.append({
                        "filename": image_filename,
                        "path": str(image_path),
                        "page": page_num + 1,
                        "format": image_ext
                    })
            
            doc.close()
            
        except Exception as e:
            print(f"Image extraction error: {e}")
        
        return images
    
    def get_table_of_contents(self, pdf_path: Path) -> List[Dict]:
        """
        Extract table of contents from PDF
        
        Args:
            pdf_path: Path to PDF manual
        
        Returns:
            List of TOC entries with titles and page numbers
        """
        toc = []
        
        try:
            doc = fitz.open(pdf_path)
            toc_data = doc.get_toc()
            
            for entry in toc_data:
                level, title, page = entry
                toc.append({
                    "level": level,
                    "title": title,
                    "page": page
                })
            
            doc.close()
            
        except Exception as e:
            print(f"TOC extraction error: {e}")
        
        return toc


# Example usage
if __name__ == "__main__":
    parser = OEMManualParser()
    
    # List all Lenovo manuals
    lenovo_manuals = parser.get_brand_manuals("lenovo")
    print(f"Found {len(lenovo_manuals)} Lenovo manuals")
    
    if lenovo_manuals:
        manual = lenovo_manuals[0]
        print(f"\nProcessing: {manual.name}")
        
        # Get TOC
        toc = parser.get_table_of_contents(manual)
        print(f"TOC entries: {len(toc)}")
        
        # Find battery procedures
        battery_procedures = parser.find_repair_procedures(manual, "battery")
        print(f"Battery procedures found: {len(battery_procedures)}")
