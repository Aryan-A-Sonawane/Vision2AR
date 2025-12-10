"""
PDF Manual Extractor - Extracts repair knowledge from OEM manuals
Converts PDFs to structured knowledge base for ML diagnosis
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple
import re


class ManualExtractor:
    """Extract repair procedures from OEM PDF manuals"""
    
    def __init__(self, manuals_dir: str = "manuals"):
        self.manuals_dir = Path(manuals_dir)
        self.knowledge_base = []
        
    def extract_all_manuals(self) -> List[Dict]:
        """Extract knowledge from all PDF manuals"""
        
        print("📚 Extracting knowledge from OEM manuals...")
        
        # Find all PDFs
        pdf_files = list(self.manuals_dir.rglob("*.pdf"))
        print(f"Found {len(pdf_files)} manual PDFs")
        
        for pdf_path in pdf_files:
            print(f"\n  Processing: {pdf_path.name}")
            try:
                knowledge = self._extract_pdf(pdf_path)
                self.knowledge_base.extend(knowledge)
                print(f"    ✓ Extracted {len(knowledge)} procedures")
            except Exception as e:
                print(f"    ✗ Error: {e}")
        
        print(f"\n✓ Total procedures extracted: {len(self.knowledge_base)}")
        return self.knowledge_base
    
    def _extract_pdf(self, pdf_path: Path) -> List[Dict]:
        """Extract repair procedures from a single PDF"""
        
        try:
            import fitz  # PyMuPDF
        except ImportError:
            print("⚠ PyMuPDF not installed. Install with: pip install PyMuPDF")
            return self._extract_pdf_fallback(pdf_path)
        
        knowledge = []
        doc = fitz.open(pdf_path)
        
        # Determine brand from path
        brand = pdf_path.parent.name
        manual_type = self._classify_manual_type(pdf_path.name)
        
        full_text = ""
        images = []
        
        # Extract text and images from each page
        for page_num, page in enumerate(doc):
            # Extract text
            text = page.get_text()
            full_text += f"\n--- Page {page_num + 1} ---\n{text}"
            
            # Extract images
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_data = {
                        "page": page_num + 1,
                        "format": base_image["ext"],
                        "size": len(base_image["image"]),
                        "xref": xref
                    }
                    images.append(image_data)
                except:
                    pass
        
        doc.close()
        
        # Parse procedures from text
        procedures = self._parse_procedures(full_text, brand, manual_type)
        
        # Add metadata
        for proc in procedures:
            proc["source_file"] = pdf_path.name
            proc["brand"] = brand
            proc["manual_type"] = manual_type
            proc["total_images"] = len(images)
        
        return procedures
    
    def _extract_pdf_fallback(self, pdf_path: Path) -> List[Dict]:
        """Fallback extraction using pdfplumber"""
        
        try:
            import pdfplumber
        except ImportError:
            print("⚠ pdfplumber not installed. Install with: pip install pdfplumber")
            return []
        
        knowledge = []
        brand = pdf_path.parent.name
        manual_type = self._classify_manual_type(pdf_path.name)
        
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += f"\n{text}\n"
        
        procedures = self._parse_procedures(full_text, brand, manual_type)
        
        for proc in procedures:
            proc["source_file"] = pdf_path.name
            proc["brand"] = brand
            proc["manual_type"] = manual_type
        
        return procedures
    
    def _classify_manual_type(self, filename: str) -> str:
        """Determine manual type from filename"""
        
        filename_lower = filename.lower()
        
        if "hardware" in filename_lower or "maintenance" in filename_lower:
            return "hardware_maintenance"
        elif "service" in filename_lower:
            return "service_manual"
        elif "user" in filename_lower or "guide" in filename_lower:
            return "user_guide"
        elif "thinkpad" in filename_lower or "ideapad" in filename_lower:
            return "product_manual"
        else:
            return "general_manual"
    
    def _parse_procedures(self, text: str, brand: str, manual_type: str) -> List[Dict]:
        """Parse repair procedures from manual text"""
        
        procedures = []
        
        # Common issues to look for
        issue_patterns = [
            (r"(?:won\'t|not|no|cannot)\s+(?:turn\s+on|boot|start|power)", "no_boot"),
            (r"(?:black|blank|dark)\s+screen", "black_screen"),
            (r"(?:overheat|hot|thermal)", "overheating"),
            (r"(?:battery|charging)\s+(?:issue|problem|not)", "battery_issue"),
            (r"(?:fan|noise|loud)", "fan_issue"),
            (r"(?:keyboard|key)\s+(?:not|stuck|broken)", "keyboard_issue"),
            (r"(?:slow|performance|lag)", "performance_issue"),
            (r"(?:wifi|wireless|network)\s+(?:not|issue)", "wifi_issue"),
            (r"(?:display|lcd|screen)\s+(?:crack|damage|broken)", "screen_damage"),
            (r"(?:hard\s+drive|hdd|ssd)\s+(?:fail|error|not)", "storage_issue")
        ]
        
        # Split text into sections
        lines = text.split('\n')
        current_section = []
        
        for i, line in enumerate(lines):
            current_section.append(line)
            
            # Check if this section describes a repair procedure
            section_text = '\n'.join(current_section[-50:])  # Last 50 lines
            
            for pattern, issue_type in issue_patterns:
                if re.search(pattern, section_text, re.IGNORECASE):
                    # Extract solution steps
                    steps = self._extract_steps(section_text)
                    
                    if len(steps) > 0:
                        procedures.append({
                            "issue_type": issue_type,
                            "symptoms": self._extract_symptoms(section_text),
                            "solution_steps": steps,
                            "tools_needed": self._extract_tools(section_text),
                            "warnings": self._extract_warnings(section_text),
                            "raw_text": section_text[-1000:],  # Last 1000 chars
                            "confidence": 0.7 if len(steps) > 3 else 0.5
                        })
        
        return procedures
    
    def _extract_steps(self, text: str) -> List[str]:
        """Extract step-by-step instructions"""
        
        steps = []
        
        # Look for numbered steps
        step_pattern = r'(?:^|\n)\s*(\d+[\.\)]\s*.+?)(?=\n\s*\d+[\.\)]|\n\n|$)'
        matches = re.findall(step_pattern, text, re.MULTILINE)
        
        if matches:
            steps = [m.strip() for m in matches]
        
        # Look for bullet points
        if not steps:
            bullet_pattern = r'(?:^|\n)\s*[•\-\*]\s*(.+?)(?=\n\s*[•\-\*]|\n\n|$)'
            matches = re.findall(bullet_pattern, text, re.MULTILINE)
            if matches:
                steps = [m.strip() for m in matches]
        
        # Clean up steps
        steps = [s for s in steps if len(s) > 10 and len(s) < 300]
        
        return steps[:20]  # Max 20 steps
    
    def _extract_symptoms(self, text: str) -> List[str]:
        """Extract symptom descriptions"""
        
        symptoms = []
        
        symptom_indicators = [
            r"symptom[s]?:?\s*(.+)",
            r"problem:?\s*(.+)",
            r"issue:?\s*(.+)",
            r"if\s+(.+?),\s+then"
        ]
        
        for pattern in symptom_indicators:
            matches = re.findall(pattern, text, re.IGNORECASE)
            symptoms.extend([m.strip()[:200] for m in matches])
        
        return symptoms[:5]
    
    def _extract_tools(self, text: str) -> List[str]:
        """Extract required tools"""
        
        tools = []
        
        # Common tools
        tool_keywords = [
            "screwdriver", "torx", "phillips", "flathead",
            "thermal paste", "spudger", "pry tool",
            "multimeter", "esd", "antistatic",
            "hex", "allen", "tweezers"
        ]
        
        text_lower = text.lower()
        for tool in tool_keywords:
            if tool in text_lower:
                tools.append(tool.title())
        
        return list(set(tools))[:10]
    
    def _extract_warnings(self, text: str) -> List[str]:
        """Extract warnings and cautions"""
        
        warnings = []
        
        warning_pattern = r'(?:WARNING|CAUTION|IMPORTANT|DANGER|NOTE):?\s*(.+?)(?=\n\n|WARNING|CAUTION|$)'
        matches = re.findall(warning_pattern, text, re.IGNORECASE | re.DOTALL)
        
        warnings = [m.strip()[:300] for m in matches]
        
        return warnings[:5]
    
    def save_knowledge_base(self, output_file: str = "knowledge_base.json"):
        """Save extracted knowledge to JSON"""
        
        output_path = Path(output_file)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Knowledge base saved to: {output_path}")
        print(f"  Total procedures: {len(self.knowledge_base)}")
        
        # Print summary
        issue_types = {}
        for proc in self.knowledge_base:
            issue_type = proc.get('issue_type', 'unknown')
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        print("\n📊 Procedures by issue type:")
        for issue, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {issue}: {count}")
    
    def get_procedures_for_issue(self, issue_type: str) -> List[Dict]:
        """Get all procedures for a specific issue type"""
        
        return [p for p in self.knowledge_base if p.get('issue_type') == issue_type]


if __name__ == "__main__":
    # Extract knowledge from all manuals
    extractor = ManualExtractor("../manuals")
    extractor.extract_all_manuals()
    extractor.save_knowledge_base("knowledge_base.json")
    
    # Test: Get procedures for "no boot" issue
    print("\n" + "="*60)
    print("Sample: Procedures for 'no_boot' issue")
    print("="*60)
    
    no_boot_procedures = extractor.get_procedures_for_issue("no_boot")
    if no_boot_procedures:
        proc = no_boot_procedures[0]
        print(f"\nFrom: {proc['source_file']} ({proc['brand']})")
        print(f"Steps: {len(proc['solution_steps'])}")
        print(f"\nFirst 3 steps:")
        for i, step in enumerate(proc['solution_steps'][:3], 1):
            print(f"  {i}. {step}")
