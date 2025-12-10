"""
Simplified Manual Extractor - Focus on Quality Over Quantity
Extracts only clear, structured repair procedures from OEM PDFs
"""

import fitz  # PyMuPDF
import json
import re
from pathlib import Path
from typing import List, Dict

class SimplifiedManualExtractor:
    """Extract high-quality repair procedures from PDFs"""
    
    # Focus on these high-value issues
    ISSUE_PATTERNS = {
        'no_boot': [
            r'computer (?:does not|doesn\'t|won\'t|cannot) (?:start|boot|turn on|power on)',
            r'no power',
            r'will not start',
            r'won\'t boot',
            r'system does not start'
        ],
        'overheating': [
            r'overheat(?:ing)?',
            r'thermal',
            r'fan (?:noise|loud|error)',
            r'temperature (?:high|too hot)',
            r'cooling'
        ],
        'battery_issue': [
            r'battery (?:not charging|problem|issue|won\'t charge)',
            r'power adapter',
            r'battery life',
            r'charge (?:problem|issue)'
        ],
        'black_screen': [
            r'black screen',
            r'no display',
            r'screen (?:blank|dark)',
            r'display (?:not working|problem)'
        ],
        'fan_issue': [
            r'fan (?:not working|error|noise)',
            r'cooling fan',
            r'fan assembly'
        ]
    }
    
    def __init__(self, manuals_dir: str):
        self.manuals_dir = Path(manuals_dir)
        self.procedures = []
    
    def extract_all(self):
        """Extract from all PDFs"""
        print("📚 Extracting knowledge from OEM manuals...")
        
        pdf_files = list(self.manuals_dir.rglob("*.pdf"))
        print(f"Found {len(pdf_files)} manual PDFs")
        
        for pdf_path in pdf_files:
            print(f"\n  Processing: {pdf_path.name}")
            self._extract_from_pdf(pdf_path)
        
        print(f"\n✓ Total high-quality procedures: {len(self.procedures)}")
        return self.procedures
    
    def _extract_from_pdf(self, pdf_path: Path):
        """Extract procedures from single PDF"""
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            
            # Extract all text
            for page in doc:
                full_text += page.get_text()
            
            # Find relevant sections
            procedures_found = 0
            
            for issue_type, patterns in self.ISSUE_PATTERNS.items():
                for pattern in patterns:
                    matches = list(re.finditer(pattern, full_text, re.IGNORECASE))
                    
                    for match in matches[:3]:  # Max 3 per pattern
                        # Extract context around match (500 chars before and after)
                        start = max(0, match.start() - 500)
                        end = min(len(full_text), match.end() + 2000)
                        context = full_text[start:end]
                        
                        # Try to find structured steps
                        steps = self._extract_steps(context)
                        
                        if steps and len(steps) >= 2:  # Need at least 2 steps
                            procedure = {
                                'issue_type': issue_type,
                                'symptoms': [match.group()],
                                'solution_steps': steps,
                                'tools_needed': self._extract_tools(context),
                                'warnings': self._extract_warnings(context),
                                'raw_text': context,
                                'confidence': 0.8,
                                'source_file': pdf_path.name,
                                'brand': self._get_brand(pdf_path),
                                'manual_type': 'service_manual'
                            }
                            
                            self.procedures.append(procedure)
                            procedures_found += 1
            
            print(f"    ✓ Extracted {procedures_found} procedures")
            doc.close()
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    def _extract_steps(self, text: str) -> List[str]:
        """Extract numbered/bulleted steps"""
        steps = []
        
        # Pattern 1: Numbered steps (1., 2., 3.)
        numbered = re.findall(r'^\s*(\d+)\.\s*(.+?)(?=^\s*\d+\.|$)', text, re.MULTILINE | re.DOTALL)
        if numbered:
            steps = [step[1].strip() for step in numbered if len(step[1].strip()) > 10]
        
        # Pattern 2: Lettered steps (a., b., c.)
        if not steps:
            lettered = re.findall(r'^\s*([a-z])\.\s*(.+?)(?=^\s*[a-z]\.|$)', text, re.MULTILINE | re.DOTALL)
            if lettered:
                steps = [step[1].strip() for step in lettered if len(step[1].strip()) > 10]
        
        # Pattern 3: Bullet points
        if not steps:
            bulleted = re.findall(r'^\s*[•●○▪]\s*(.+?)(?=^\s*[•●○▪]|$)', text, re.MULTILINE | re.DOTALL)
            if bulleted:
                steps = [step.strip() for step in bulleted if len(step.strip()) > 10]
        
        # Clean steps
        cleaned = []
        for step in steps[:15]:  # Max 15 steps
            # Remove excess whitespace and newlines
            clean = ' '.join(step.split())
            if len(clean) > 20 and len(clean) < 500:
                cleaned.append(clean)
        
        return cleaned
    
    def _extract_tools(self, text: str) -> List[str]:
        """Extract tool requirements"""
        tools = []
        tool_keywords = ['screwdriver', 'torx', 'phillips', 'thermal paste', 
                         'anti-static', 'spudger', 'pliers', 'tool']
        
        text_lower = text.lower()
        for keyword in tool_keywords:
            if keyword in text_lower:
                # Find sentence containing the keyword
                sentences = text.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        tools.append(sentence.strip())
                        break
        
        return tools[:3]
    
    def _extract_warnings(self, text: str) -> List[str]:
        """Extract CAUTION/WARNING sections"""
        warnings = []
        
        warning_patterns = [
            r'(?:CAUTION|WARNING|IMPORTANT|NOTE):\s*(.+?)(?=\n\n|\n[A-Z]|$)',
            r'(?:Caution|Warning|Important|Note):\s*(.+?)(?=\n\n|\n[A-Z]|$)'
        ]
        
        for pattern in warning_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                clean = ' '.join(match.split())
                if len(clean) > 20:
                    warnings.append(clean)
        
        return warnings[:2]
    
    def _get_brand(self, pdf_path: Path) -> str:
        """Determine brand from path"""
        path_lower = str(pdf_path).lower()
        
        if 'lenovo' in path_lower or 'lenevo' in path_lower:
            return 'lenovo'
        elif 'dell' in path_lower:
            return 'dell'
        elif 'hp' in path_lower:
            return 'hp'
        else:
            return 'unknown'
    
    def save_knowledge_base(self, output_path: str):
        """Save extracted knowledge to JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.procedures, f, indent=2, ensure_ascii=False)
        
        # Print stats
        print("\n" + "="*70)
        print(f"✓ Knowledge base saved to: {output_path}")
        print(f"  Total procedures: {len(self.procedures)}")
        
        # Show breakdown
        issue_counts = {}
        for proc in self.procedures:
            issue = proc['issue_type']
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        print("\n📊 Procedures by issue type:")
        for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
            print(f"  {issue}: {count}")


if __name__ == "__main__":
    import sys
    
    manuals_dir = Path(__file__).parent.parent / "manuals"
    output_path = Path(__file__).parent.parent / "backend" / "knowledge_base_v2.json"
    
    print("="*70)
    print(" Simplified OEM Manual Extraction (Quality Focus)")
    print("="*70)
    print()
    
    extractor = SimplifiedManualExtractor(manuals_dir)
    extractor.extract_all()
    extractor.save_knowledge_base(output_path)
    
    print("\n✓ Extraction complete!")
    print(f"  Knowledge base: {output_path}")
    print()
