"""
YouTube Transcript Fetcher

This module fetches and processes transcripts from YouTube videos
of financial content creators defined in the configuration file.
"""

import os
import json
import logging
import yaml
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('transcript_fetcher')

class TranscriptFetcher:
    """Fetches and processes YouTube transcripts from specified channels."""
    
    def __init__(self, config_path: str, storage_path: str):
        """
        Initialize the TranscriptFetcher.
        
        Args:
            config_path: Path to the settings.yaml file
            storage_path: Path to store the transcript data
        """
        self.config_path = config_path
        self.storage_path = storage_path
        self.config = self._load_config()
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        # For demonstration, we're using dummy YouTube API key
        # In production, this would come from the config
        self.youtube_api_key = "DUMMY_YOUTUBE_API_KEY"  
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
            
    def _get_channel_videos(self, channel_id: str, published_after: datetime) -> List[Dict[str, Any]]:
        """
        Get recent videos from a YouTube channel.
        
        Args:
            channel_id: YouTube channel ID
            published_after: Only fetch videos published after this date
            
        Returns:
            List of video details (id, title, published_at)
        """
        # NOTE: This is a dummy implementation
        # In a real implementation, we would use the YouTube Data API
        logger.info(f"Fetching videos for channel {channel_id}")
        
        # For demonstration, return dummy data
        return [
            {
                "id": "dummy_video_id_1",
                "title": "Latest Market Analysis - March 2025",
                "published_at": datetime.now().isoformat(),
                "channel_title": "Coin Bureau"
            },
            {
                "id": "dummy_video_id_2",
                "title": "Bitcoin Price Prediction 2025",
                "published_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "channel_title": "Benjamin Cowen"
            }
        ]
    
    def _fetch_transcript(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch transcript for a specific YouTube video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Transcript as a list of segments with text and timestamps
        """
        try:
            # NOTE: In a real implementation, this would call YouTubeTranscriptApi
            logger.info(f"Fetching transcript for video {video_id}")
            
            # For demonstration, return dummy transcript data
            if video_id == "dummy_video_id_1":
                return [
                    {"text": "Today we're looking at Bitcoin's price action", "start": 0.0, "duration": 4.5},
                    {"text": "The market seems bullish as institutional adoption increases", "start": 4.5, "duration": 5.0},
                    {"text": "Ethereum's latest upgrade has significant implications", "start": 9.5, "duration": 4.8}
                ]
            elif video_id == "dummy_video_id_2":
                return [
                    {"text": "Let's analyze the Bitcoin logarithmic regression band", "start": 0.0, "duration": 5.2},
                    {"text": "We can see clear support at the current levels", "start": 5.2, "duration": 4.3},
                    {"text": "The next resistance is at sixty-thousand dollars", "start": 9.5, "duration": 4.1}
                ]
            return None
        except Exception as e:
            logger.error(f"Error fetching transcript for video {video_id}: {e}")
            return None
            
    def _save_transcript(self, video_id: str, video_title: str, channel_title: str, 
                         published_at: str, transcript: List[Dict[str, Any]]) -> bool:
        """
        Save transcript data to storage.
        
        Args:
            video_id: YouTube video ID
            video_title: Title of the video
            channel_title: Name of the channel
            published_at: Publication timestamp
            transcript: Transcript data
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            file_path = os.path.join(self.storage_path, f"{video_id}.json")
            data = {
                "video_id": video_id,
                "title": video_title,
                "channel": channel_title,
                "published_at": published_at,
                "fetched_at": datetime.now().isoformat(),
                "transcript": transcript
            }
            
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=2)
            
            logger.info(f"Saved transcript for video {video_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving transcript for video {video_id}: {e}")
            return False
    
    def fetch_recent_transcripts(self, days_back: int = 7) -> int:
        """
        Fetch transcripts for recent videos from all configured channels.
        
        Args:
            days_back: Number of days to look back for videos
            
        Returns:
            Number of transcripts successfully fetched
        """
        if not self.config.get('youtube', {}).get('channels'):
            logger.error("No YouTube channels configured")
            return 0
            
        published_after = datetime.now() - timedelta(days=days_back)
        successful_fetches = 0
        
        for channel in self.config['youtube']['channels']:
            channel_id = channel.get('channel_id')
            if not channel_id:
                continue
                
            videos = self._get_channel_videos(channel_id, published_after)
            for video in videos:
                transcript = self._fetch_transcript(video['id'])
                if transcript:
                    save_success = self._save_transcript(
                        video['id'], 
                        video['title'], 
                        video['channel_title'],
                        video['published_at'],
                        transcript
                    )
                    if save_success:
                        successful_fetches += 1
        
        logger.info(f"Fetched {successful_fetches} transcripts")
        return successful_fetches
        
    def get_all_transcripts(self) -> List[Dict[str, Any]]:
        """
        Load all stored transcripts.
        
        Returns:
            List of transcript data with metadata
        """
        transcripts = []
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.storage_path, filename), 'r') as file:
                        transcripts.append(json.load(file))
                except Exception as e:
                    logger.error(f"Error loading transcript {filename}: {e}")
        
        # Sort by published date, newest first
        transcripts.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        return transcripts

# Example usage
if __name__ == "__main__":
    # This is for testing the module directly
    fetcher = TranscriptFetcher(
        config_path="../config/settings.yaml",
        storage_path="../data/transcripts"
    )
    num_fetched = fetcher.fetch_recent_transcripts(days_back=7)
    print(f"Fetched {num_fetched} transcripts")
    
    all_transcripts = fetcher.get_all_transcripts()
    print(f"Total stored transcripts: {len(all_transcripts)}")