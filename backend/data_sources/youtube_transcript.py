"""
YouTube Transcript Fetcher
Extract repair instructions from YouTube video transcripts
"""

import re
from typing import List, Dict, Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import requests
from urllib.parse import urlparse, parse_qs

class YouTubeTranscriptFetcher:
    """
    Fetch and parse YouTube video transcripts for repair guides
    """
    
    def __init__(self):
        self.session = requests.Session()
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL
        
        Args:
            url: YouTube URL (watch, embed, shortened)
        
        Returns:
            Video ID or None
        """
        # Pattern 1: youtube.com/watch?v=VIDEO_ID
        if "youtube.com/watch" in url:
            parsed = urlparse(url)
            query = parse_qs(parsed.query)
            return query.get("v", [None])[0]
        
        # Pattern 2: youtu.be/VIDEO_ID
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        
        # Pattern 3: youtube.com/embed/VIDEO_ID
        if "youtube.com/embed/" in url:
            return url.split("embed/")[1].split("?")[0]
        
        return None
    
    def get_transcript(self, video_id: str, languages: List[str] = ["en"]) -> Optional[List[Dict]]:
        """
        Get transcript for YouTube video
        
        Args:
            video_id: YouTube video ID
            languages: Preferred languages (default: English)
        
        Returns:
            List of transcript segments with timestamps
        """
        try:
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=languages
            )
            return transcript
            
        except TranscriptsDisabled:
            print(f"Transcripts disabled for video: {video_id}")
            return None
        except NoTranscriptFound:
            print(f"No transcript found for video: {video_id}")
            return None
        except Exception as e:
            print(f"Transcript fetch error: {e}")
            return None
    
    def parse_repair_steps(self, transcript: List[Dict], device_model: str) -> List[Dict]:
        """
        Parse transcript to extract repair steps
        
        Args:
            transcript: Raw transcript from YouTube
            device_model: Device model for context
        
        Returns:
            List of repair steps with timestamps
        """
        # Combine transcript into full text
        full_text = " ".join([seg["text"] for seg in transcript])
        
        # Detect step markers
        steps = []
        current_step = None
        
        for segment in transcript:
            text = segment["text"].lower()
            start_time = segment["start"]
            
            # Look for step indicators
            if any(indicator in text for indicator in [
                "step one", "step 1", "first step", "first,",
                "step two", "step 2", "second step", "second,",
                "step three", "step 3", "third step", "third,",
                "next step", "now we", "then we", "after that"
            ]):
                # Start new step
                if current_step:
                    steps.append(current_step)
                
                current_step = {
                    "timestamp_start": start_time,
                    "text": segment["text"],
                    "actions": []
                }
            
            elif current_step:
                # Add to current step
                current_step["text"] += " " + segment["text"]
                
                # Detect actions
                if any(action in text for action in [
                    "remove", "unscrew", "disconnect", "pull", "lift",
                    "replace", "install", "connect", "screw", "insert"
                ]):
                    current_step["actions"].append({
                        "timestamp": start_time,
                        "action": segment["text"]
                    })
        
        # Add last step
        if current_step:
            steps.append(current_step)
        
        return steps
    
    def search_repair_videos(self, device_model: str, issue: str) -> List[Dict]:
        """
        Search for repair videos (using YouTube Data API would require API key)
        This is a placeholder for manual URL input
        
        Args:
            device_model: Device model
            issue: Problem description
        
        Returns:
            List of video metadata (requires YouTube Data API key)
        """
        # Note: Actual implementation would use YouTube Data API v3
        # For now, return empty list - videos should be added manually
        print("YouTube search requires API key. Add video URLs manually.")
        return []
    
    def extract_key_moments(self, transcript: List[Dict]) -> List[Dict]:
        """
        Extract key moments from transcript (screw removal, component ID, etc.)
        
        Args:
            transcript: Video transcript
        
        Returns:
            List of key moments with timestamps
        """
        key_moments = []
        
        keywords = {
            "screw_removal": ["screw", "unscrew", "remove screw", "phillips"],
            "cable_disconnect": ["disconnect", "unplug", "cable", "ribbon cable"],
            "component_removal": ["remove", "take out", "lift", "pull out"],
            "warning": ["careful", "caution", "warning", "don't", "avoid"],
            "tool_required": ["tool", "screwdriver", "spudger", "tweezers"]
        }
        
        for segment in transcript:
            text = segment["text"].lower()
            timestamp = segment["start"]
            
            for category, terms in keywords.items():
                if any(term in text for term in terms):
                    key_moments.append({
                        "category": category,
                        "timestamp": timestamp,
                        "text": segment["text"],
                        "video_timestamp": self._format_timestamp(timestamp)
                    })
                    break
        
        return key_moments
    
    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def get_video_metadata(self, video_id: str) -> Dict:
        """
        Get video title, duration, channel (requires scraping or API)
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            Video metadata
        """
        # This would require YouTube Data API or scraping
        # For now, return basic info
        return {
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "embed_url": f"https://www.youtube.com/embed/{video_id}"
        }


# Example usage
if __name__ == "__main__":
    fetcher = YouTubeTranscriptFetcher()
    
    # Example: Lenovo IdeaPad repair video
    test_url = "https://www.youtube.com/watch?v=EXAMPLE_ID"
    video_id = fetcher.extract_video_id(test_url)
    
    if video_id:
        print(f"Video ID: {video_id}")
        
        # Get transcript
        transcript = fetcher.get_transcript(video_id)
        
        if transcript:
            print(f"Transcript segments: {len(transcript)}")
            
            # Parse repair steps
            steps = fetcher.parse_repair_steps(transcript, "Lenovo IdeaPad 5")
            print(f"Repair steps found: {len(steps)}")
            
            # Extract key moments
            moments = fetcher.extract_key_moments(transcript)
            print(f"Key moments: {len(moments)}")
