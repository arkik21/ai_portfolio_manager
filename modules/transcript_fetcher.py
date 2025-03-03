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
from googleapiclient.errors import HttpError

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
        
        self.youtube_api_key = self.config.get('apis', {}).get('youtube_api', {}).get('api_key')
        if not self.youtube_api_key:
            logger.error("YouTube API key not found in config.")
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML files, prioritizing secrets.yaml."""
        configs = {}
        settings_path = self.config_path # settings.yaml path is already in self.config_path
        secrets_path = os.path.join(os.path.dirname(settings_path), 'secrets.yaml')

        # Load settings.yaml first
        try:
            with open(settings_path, 'r') as settings_file:
                settings_config = yaml.safe_load(settings_file)
                if settings_config: # Check if settings_config is not None
                    configs.update(settings_config)
                    logger.info(f"Loaded config from: {settings_path}")
                else:
                    logger.warning(f"Settings config file {settings_path} is empty or invalid YAML.")
        except Exception as e:
            logger.error(f"Failed to load settings config from {settings_path}: {e}")

        # Load secrets.yaml and override settings if it exists
        if os.path.exists(secrets_path):
            try:
                with open(secrets_path, 'r') as secrets_file:
                    secrets_config = yaml.safe_load(secrets_file)
                    if secrets_config: # Check if secrets_config is not None
                        configs.update(secrets_config) # Secrets override settings
                        logger.info(f"Loaded config from: {secrets_path}")
                    else:
                        logger.warning(f"Secrets config file {secrets_path} is empty or invalid YAML.")
            except Exception as e:
                logger.error(f"Failed to load secrets config {secrets_path}: {e}")

        logger.debug(f"Loaded Configuration: {configs}") # Log the final loaded config for inspection
        return configs
            
    def _get_recent_channel_videos(self, channel_id: str, published_after: datetime) -> List[Dict[str, Any]]:
        """
        Get recent videos from a YouTube channel using YouTube Data API search.

        Args:
            channel_id: YouTube channel ID
            published_after: Only fetch videos published after this date

        Returns:
            List of video details (id, title, published_at)
        """
        logger.info(f"Fetching recent videos for channel {channel_id} using YouTube Data API search")
        youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)

        videos_data = []
        try:
            # Corrected API method call and added 'id' to part parameter
            request = youtube.search().list(
                part='id,snippet',  # Include both id and snippet parts
                channelId=channel_id,
                order='date',
                publishedAfter=published_after.isoformat("T") + "Z",
                type='video',
                maxResults=1  # Maximum allowed per API request
            )
            response = request.execute()

            for item in response.get('items', []):
                video_data = {
                    "id": item['id']['videoId'],
                    "title": item['snippet']['title'],
                    "published_at": item['snippet']['publishedAt'],
                    "channel_title": item['snippet']['channelTitle']
                }
                videos_data.append(video_data)

        except HttpError as e:
            logger.error(f"YouTube API error fetching videos for channel {channel_id}: {e}")
            return []
        except KeyError as e:
            logger.error(f"Missing expected field in API response: {e}")
            return []

        return videos_data

    
    def _fetch_transcript(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch transcript for a specific YouTube video using youtube_transcript_api.

        Args:
            video_id: YouTube video ID

        Returns:
            Transcript as a list of segments with text and timestamps
        """
        logger.info(f"Fetching transcript for video {video_id} using YouTubeTranscriptApi")
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return transcript
        except Exception as e:
            logger.error(f"Error fetching transcript for video {video_id}: {e}")
            return None
            
    def _save_transcript(self, video_id: str, video_title: str, channel_title: str,
                         published_at: str, transcript: List[Dict[str, Any]]) -> bool:
        """
        Save transcript data to storage, both as JSON and plain text.
        """
        try:
            # Save JSON format (as before)
            file_path_json = os.path.join(self.storage_path, f"{video_id}.json")
            data = {
                "video_id": video_id,
                "title": video_title,
                "channel": channel_title,
                "published_at": published_at,
                "fetched_at": datetime.now().isoformat(),
                "transcript": transcript
            }
            with open(file_path_json, 'w') as file:
                json.dump(data, file, indent=2)
            logger.info(f"Saved transcript (JSON) for video {video_id}")

            # Save plain text format
            file_path_txt = os.path.join(self.storage_path, f"{video_id}.txt")
            plain_text_transcript = self._process_transcript_to_plain_text(transcript) # Call new function
            with open(file_path_txt, 'w', encoding='utf-8') as file: # Ensure UTF-8 encoding
                file.write(plain_text_transcript)
            logger.info(f"Saved transcript (plain text) for video {video_id}")


            return True
        except Exception as e:
            logger.error(f"Error saving transcript for video {video_id}: {e}")
            return False

    def _process_transcript_to_plain_text(self, transcript: List[Dict[str, Any]]) -> str:
        """
        Processes the transcript JSON to create a plain text string.

        Args:
            transcript: List of transcript segments

        Returns:
            Plain text transcript as a single string
        """
        text_segments = [segment['text'] for segment in transcript] # Extract text from each segment
        plain_text = " ".join(text_segments) # Join segments with spaces
        return plain_text
    
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
                
            videos = self._get_recent_channel_videos(channel_id, published_after)
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
        config_path="config/settings.yaml", # Simplified path to settings
        storage_path="./data/transcripts"
    )
    num_fetched = fetcher.fetch_recent_transcripts(days_back=7)
    print(f"Fetched {num_fetched} transcripts")

    all_transcripts = fetcher.get_all_transcripts()
    print(f"Total stored transcripts: {len(all_transcripts)}")

    # Example of fetching videos for a specific channel and transcript for a video
    channels_config = fetcher.config.get('youtube', {}).get('channels', [])
    if channels_config:
        first_channel_id = channels_config[0].get('channel_id')
        if first_channel_id:
            videos = fetcher._get_recent_channel_videos(first_channel_id, datetime.now() - timedelta(days=7))
            if videos:
                print(f"\nVideos fetched for channel {first_channel_id}:")
                for video in videos:
                    print(f"- {video['title']} (ID: {video['id']})")

                first_video_id = videos[0]['id']
                transcript = fetcher._fetch_transcript(first_video_id)
                if transcript:
                    print(f"\nTranscript for video ID {first_video_id}:")
                    print(transcript[:2]) # Print first 2 segments of the transcript
                else:
                    print(f"No transcript fetched for video ID {first_video_id}")
            else:
                print(f"No videos fetched for channel {first_channel_id}")
        else:
            print("No channel_id found in the first channel config.")
    else:
        print("No YouTube channels configured in settings.yaml")