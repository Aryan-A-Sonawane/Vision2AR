"""
Data Ingestion Pipeline
Combines OEM manuals, iFixit guides, and YouTube transcripts
into canonical repair procedures
"""

from typing import List, Dict, Optional
from pathlib import Path
import json
from datetime import datetime

from data_sources.ifixit_api import IFixitAPI
from data_sources.oem_manual_parser import OEMManualParser
from data_sources.youtube_transcript import YouTubeTranscriptFetcher
from tutorial.step_merger import TutorialMerger, RepairStep, SourceType, RiskLevel

class DataIngestionPipeline:
    """
    Multi-source data ingestion and merging pipeline
    Priority: OEM → iFixit → YouTube
    """
    
    def __init__(self, output_dir: str = "./ingested_data"):
        self.ifixit = IFixitAPI()
        self.oem_parser = OEMManualParser()
        self.youtube = YouTubeTranscriptFetcher()
        self.merger = None  # Will be initialized per device
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def ingest_device(
        self,
        device_model: str,
        brand: str,
        component: str,
        youtube_urls: Optional[List[str]] = None
    ) -> Dict:
        """
        Ingest repair data for a specific device component
        
        Args:
            device_model: Device model (e.g., "IdeaPad 5")
            brand: Brand (e.g., "lenovo")
            component: Component to repair (e.g., "battery")
            youtube_urls: Optional YouTube video URLs
        
        Returns:
            Merged repair procedure
        """
        print(f"\n{'='*60}")
        print(f"INGESTING: {brand} {device_model} - {component}")
        print(f"{'='*60}\n")
        
        # Initialize merger for this device
        self.merger = TutorialMerger(brand=brand, product=device_model)
        
        # Step 1: Get OEM manual data (PRIMARY SOURCE)
        print("1️⃣ Extracting from OEM manuals...")
        oem_data = self._ingest_oem_manuals(brand, component)
        
        # Step 2: Get iFixit data (ENHANCEMENT SOURCE)
        print("\n2️⃣ Fetching from iFixit...")
        ifixit_data = self._ingest_ifixit(device_model, component)
        
        # Step 3: Get YouTube data (VISUAL SOURCE)
        print("\n3️⃣ Fetching YouTube transcripts...")
        youtube_data = self._ingest_youtube(youtube_urls) if youtube_urls else []
        
        # Step 4: Merge all sources
        print("\n4️⃣ Merging sources...")
        merged_procedure = self._merge_sources(
            device_model=device_model,
            brand=brand,
            component=component,
            oem_data=oem_data,
            ifixit_data=ifixit_data,
            youtube_data=youtube_data
        )
        
        # Step 5: Save to disk
        self._save_procedure(merged_procedure)
        
        print(f"\n✅ Ingestion complete for {brand} {device_model} - {component}")
        print(f"   Total steps: {len(merged_procedure['steps'])}")
        print(f"   Sources used: {', '.join(merged_procedure['sources_used'])}")
        
        return merged_procedure
    
    def _ingest_oem_manuals(self, brand: str, component: str) -> List[Dict]:
        """Extract procedures from OEM manuals"""
        manuals = self.oem_parser.get_brand_manuals(brand)
        
        if not manuals:
            print(f"   ⚠️ No OEM manuals found for {brand}")
            return []
        
        print(f"   Found {len(manuals)} manual(s)")
        
        all_procedures = []
        for manual in manuals:
            print(f"   Processing: {manual.name}")
            procedures = self.oem_parser.find_repair_procedures(manual, component)
            all_procedures.extend(procedures)
        
        print(f"   ✅ Extracted {len(all_procedures)} procedure(s)")
        return all_procedures
    
    def _ingest_ifixit(self, device_model: str, component: str) -> List[Dict]:
        """Fetch guides from iFixit"""
        # Search for device
        search_results = self.ifixit.search_device(device_model)
        
        if not search_results:
            print(f"   ⚠️ No iFixit guides found for {device_model}")
            return []
        
        print(f"   Found {len(search_results)} device(s)")
        
        guides = []
        for result in search_results[:3]:  # Top 3 results
            # Search for component-specific guide
            device_name = result.get("title", "")
            print(f"   Searching guides for: {device_name}")
            
            # Get device guides
            guide_search = self.ifixit.search_device(f"{device_model} {component}")
            
            for guide_result in guide_search:
                if guide_result.get("type") == "guide":
                    guide_id = guide_result.get("guideid")
                    guide = self.ifixit.get_guide(guide_id)
                    
                    if guide:
                        guides.append(guide)
                        print(f"   ✅ Fetched: {guide['title']}")
        
        return guides
    
    def _ingest_youtube(self, video_urls: List[str]) -> List[Dict]:
        """Fetch transcripts from YouTube videos"""
        if not video_urls:
            return []
        
        transcripts = []
        
        for url in video_urls:
            video_id = self.youtube.extract_video_id(url)
            
            if not video_id:
                print(f"   ⚠️ Invalid URL: {url}")
                continue
            
            print(f"   Fetching: {video_id}")
            transcript = self.youtube.get_transcript(video_id)
            
            if transcript:
                # Parse repair steps
                steps = self.youtube.parse_repair_steps(transcript, "")
                key_moments = self.youtube.extract_key_moments(transcript)
                
                transcripts.append({
                    "video_id": video_id,
                    "url": url,
                    "steps": steps,
                    "key_moments": key_moments,
                    "raw_transcript": transcript
                })
                
                print(f"   ✅ {len(steps)} steps, {len(key_moments)} key moments")
        
        return transcripts
    
    def _merge_sources(
        self,
        device_model: str,
        brand: str,
        component: str,
        oem_data: List[Dict],
        ifixit_data: List[Dict],
        youtube_data: List[Dict]
    ) -> Dict:
        """
        Merge all sources into canonical repair procedure
        Priority: OEM (spine) → iFixit (details) → YouTube (visuals)
        """
        sources_used = []
        
        # Use OEM as canonical spine
        if oem_data:
            base_steps = self._convert_oem_to_steps(oem_data[0])
            sources_used.append("OEM")
        elif ifixit_data:
            # Fallback to iFixit if no OEM data
            base_steps = self._convert_ifixit_to_steps(ifixit_data[0])
            sources_used.append("iFixit")
        elif youtube_data:
            # Last resort: YouTube
            base_steps = self._convert_youtube_to_steps(youtube_data[0])
            sources_used.append("YouTube")
        else:
            raise ValueError("No data sources available")
        
        # Enhance with iFixit details
        if ifixit_data and "iFixit" not in sources_used:
            base_steps = self._enhance_with_ifixit(base_steps, ifixit_data[0])
            sources_used.append("iFixit")
        
        # Add YouTube visual anchors
        if youtube_data and "YouTube" not in sources_used:
            base_steps = self._enhance_with_youtube(base_steps, youtube_data[0])
            sources_used.append("YouTube")
        
        # Steps are already in RepairStep format, just convert to dict
        return {
            "device_model": device_model,
            "brand": brand,
            "component": component,
            "steps": [self._step_to_dict(s) for s in base_steps],
            "sources_used": sources_used,
            "ingested_at": datetime.now().isoformat(),
            "total_steps": len(base_steps)
        }
    
    def _convert_oem_to_steps(self, oem_procedure: Dict) -> List[RepairStep]:
        """Convert OEM manual data to RepairStep objects"""
        steps = []
        
        for idx, step_text in enumerate(oem_procedure.get("steps", []), 1):
            steps.append(RepairStep(
                step_id=idx,
                action=step_text,
                source_primary=SourceType.OEM,
                source_supporting=[],
                tools=[],
                risk_level=RiskLevel.SAFE,  # Default
                image=f"assets/{oem_procedure.get('pdf_name', 'manual')}/step{idx}.jpg",
                overlay_anchors=[],
                video_timestamp=None,
                warnings=[],
                details=None
            ))
        
        return steps
    
    def _convert_ifixit_to_steps(self, ifixit_guide: Dict) -> List[RepairStep]:
        """Convert iFixit guide to RepairStep objects"""
        steps = []
        
        for step_data in ifixit_guide.get("steps", []):
            step_num = step_data["step_number"]
            
            # Combine all line texts
            action_text = step_data["title"] + ". " + " ".join(
                [line["text"] for line in step_data["lines"]]
            )
            
            # Extract tools from lines
            tools = []
            for line in step_data["lines"]:
                if "tool" in line["text"].lower():
                    tools.append(line["text"])
            
            # Get image URL
            image_url = ""
            if step_data["images"]:
                image_url = step_data["images"][0]["url"]
            
            steps.append(RepairStep(
                step_id=step_num,
                action=action_text,
                source_primary=SourceType.IFIXIT,
                source_supporting=[],
                tools=tools,
                risk_level=RiskLevel.SAFE,
                image=image_url,
                overlay_anchors=[],
                video_timestamp=None,
                warnings=[],
                details=None
            ))
        
        return steps
    
    def _convert_youtube_to_steps(self, youtube_data: Dict) -> List[RepairStep]:
        """Convert YouTube transcript to RepairStep objects"""
        steps = []
        
        for idx, step_data in enumerate(youtube_data.get("steps", []), 1):
            steps.append(RepairStep(
                step_id=idx,
                action=step_data["text"],
                source_primary=SourceType.YOUTUBE,
                source_supporting=[],
                tools=[],
                risk_level=RiskLevel.SAFE,
                image="",
                overlay_anchors=[],
                video_timestamp=f"{int(step_data['timestamp_start']//60):02d}:{int(step_data['timestamp_start']%60):02d}",
                warnings=[],
                details=None
            ))
        
        return steps
    
    def _enhance_with_ifixit(self, steps: List[RepairStep], ifixit_guide: Dict) -> List[RepairStep]:
        """Enhance OEM steps with iFixit details"""
        # Add tools and warnings from iFixit
        for step in steps:
            # Match iFixit step by similarity (simplified)
            for ifixit_step in ifixit_guide.get("steps", []):
                # Add tool details
                for line in ifixit_step["lines"]:
                    if "tool" in line["text"].lower():
                        step.tools.append(line["text"])
                    
                    # Add warnings
                    if line["level"] in ["icon_caution", "icon_reminder"]:
                        step.warnings.append(line["text"])
        
        return steps
    
    def _enhance_with_youtube(self, steps: List[RepairStep], youtube_data: Dict) -> List[RepairStep]:
        """Add YouTube video timestamps to steps"""
        key_moments = youtube_data.get("key_moments", [])
        
        for idx, step in enumerate(steps):
            if idx < len(key_moments):
                step.video_timestamp = key_moments[idx]["video_timestamp"]
        
        return steps
    
    def _step_to_dict(self, step: RepairStep) -> Dict:
        """Convert RepairStep to dictionary"""
        return {
            "step_id": step.step_id,
            "action": step.action,
            "source_primary": step.source_primary.value,
            "source_supporting": [s.value for s in step.source_supporting],
            "tools": step.tools,
            "risk_level": step.risk_level.value,
            "image": step.image,
            "overlay_anchors": step.overlay_anchors,
            "video_timestamp": step.video_timestamp,
            "warnings": step.warnings
        }
    
    def _save_procedure(self, procedure: Dict):
        """Save merged procedure to JSON file"""
        filename = f"{procedure['brand']}_{procedure['device_model']}_{procedure['component']}.json"
        filename = filename.replace(" ", "_").lower()
        
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(procedure, f, indent=2, ensure_ascii=False)
        
        print(f"   💾 Saved to: {filepath}")


# Example usage
if __name__ == "__main__":
    pipeline = DataIngestionPipeline()
    
    # Ingest Lenovo IdeaPad 5 battery replacement
    result = pipeline.ingest_device(
        device_model="IdeaPad 5",
        brand="lenovo",
        component="battery",
        youtube_urls=[
            "https://www.youtube.com/watch?v=EXAMPLE_ID_1"
        ]
    )
    
    print(f"\n📊 Final result:")
    print(f"   Steps: {result['total_steps']}")
    print(f"   Sources: {', '.join(result['sources_used'])}")
