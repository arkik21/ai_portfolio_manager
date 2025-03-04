# transcript_fetcher

YouTube Transcript Fetcher

This module fetches and processes transcripts from YouTube videos
of financial content creators defined in the configuration file.

**Module Path:** `transcript_fetcher`

## Table of Contents

### Classes

- [TranscriptFetcher](#transcriptfetcher)

## Classes

### TranscriptFetcher

Fetches and processes YouTube transcripts from specified channels.

#### Methods

##### `__init__(config_path, storage_path)`

Initialize the TranscriptFetcher.

Args:
    config_path: Path to the settings.yaml file
    storage_path: Path to store the transcript data

**Type Hints:**

- **config_path**: `str`
- **storage_path**: `str`

##### `_load_config()`

Load configuration from YAML files, prioritizing secrets.yaml.

**Type Hints:**

- **returns**: `Dict[str, Any]`

##### `_get_recent_channel_videos(channel_id, published_after)`

Get recent videos from a YouTube channel using YouTube Data API search.

Args:
    channel_id: YouTube channel ID
    published_after: Only fetch videos published after this date

Returns:
    List of video details (id, title, published_at)

**Type Hints:**

- **channel_id**: `str`
- **published_after**: `datetime`
- **returns**: `List[Dict[str, Any]]`

##### `_fetch_transcript(video_id)`

Fetch transcript for a specific YouTube video using youtube_transcript_api.

Args:
    video_id: YouTube video ID

Returns:
    Transcript as a list of segments with text and timestamps

**Type Hints:**

- **video_id**: `str`
- **returns**: `Optional[List[Dict[str, Any]]]`

##### `_save_transcript(video_id, video_title, channel_title, published_at, transcript)`

Save transcript data to storage, both as JSON and plain text.

**Type Hints:**

- **video_id**: `str`
- **video_title**: `str`
- **channel_title**: `str`
- **published_at**: `str`
- **transcript**: `List[Dict[str, Any]]`
- **returns**: `bool`

##### `_process_transcript_to_plain_text(transcript)`

Processes the transcript JSON to create a plain text string.

Args:
    transcript: List of transcript segments

Returns:
    Plain text transcript as a single string

**Type Hints:**

- **transcript**: `List[Dict[str, Any]]`
- **returns**: `str`

##### `fetch_recent_transcripts(days_back=7)`

Fetch transcripts for recent videos from all configured channels.

Args:
    days_back: Number of days to look back for videos
    
Returns:
    Number of transcripts successfully fetched

**Type Hints:**

- **days_back**: `int`
- **returns**: `int`

##### `get_all_transcripts()`

Load all stored transcripts.

Returns:
    List of transcript data with metadata

**Type Hints:**

- **returns**: `List[Dict[str, Any]]`

