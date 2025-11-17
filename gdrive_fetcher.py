"""
Google Drive File Fetcher with Caching
Handles downloading files from Google Drive links and caching them locally
"""

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import parse_qs, urlparse

import requests


class GDriveFetcher:
    """Handles fetching files from Google Drive with caching"""

    def __init__(self, cache_dir: str = None, cache_duration: int = 86400):
        """
        Initialize the Google Drive fetcher

        Args:
            cache_dir: Directory to store cached files (default: ./gdrive_cache)
            cache_duration: Cache duration in seconds (default: 86400 = 24 hours)
        """
        self.cache_dir = Path(cache_dir or "./gdrive_cache")
        self.cache_duration = cache_duration
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> dict:
        """Load cache metadata from disk"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_metadata(self):
        """Save cache metadata to disk"""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save cache metadata: {e}")

    def _get_cache_key(self, file_id: str) -> str:
        """Generate a cache key from file ID"""
        return hashlib.md5(file_id.encode()).hexdigest()

    def is_gdrive_link(self, url: str) -> bool:
        """
        Check if a URL is a Google Drive link

        Args:
            url: URL to check

        Returns:
            True if it's a Google Drive link, False otherwise
        """
        if not isinstance(url, str):
            return False

        gdrive_patterns = [
            r"drive\.google\.com/file/d/",
            r"drive\.google\.com/open\?id=",
            r"docs\.google\.com/.*/(d/|id=)",
        ]

        return any(re.search(pattern, url) for pattern in gdrive_patterns)

    def extract_file_id(self, url: str) -> Optional[str]:
        """
        Extract file ID from various Google Drive URL formats

        Supported formats:
        - https://drive.google.com/file/d/FILE_ID/view
        - https://drive.google.com/open?id=FILE_ID
        - https://docs.google.com/document/d/FILE_ID/edit

        Args:
            url: Google Drive URL

        Returns:
            File ID or None if not found
        """
        # Pattern 1: /d/FILE_ID/
        match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)

        # Pattern 2: ?id=FILE_ID or &id=FILE_ID
        match = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)

        return None

    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cached file is still valid based on age

        Args:
            cache_key: Cache key to check

        Returns:
            True if cache is valid, False otherwise
        """
        if cache_key not in self.metadata:
            return False

        cached_time = self.metadata[cache_key].get("timestamp", 0)
        current_time = time.time()
        age = current_time - cached_time

        return age < self.cache_duration

    def _get_cached_path(self, cache_key: str) -> Optional[Path]:
        """
        Get the path to a cached file if it exists and is valid

        Args:
            cache_key: Cache key

        Returns:
            Path to cached file or None if not found/invalid
        """
        if not self._is_cache_valid(cache_key):
            return None

        cached_path = Path(self.metadata[cache_key].get("path", ""))
        if cached_path.exists():
            return cached_path

        return None

    def _download_file(self, file_id: str, output_path: Path) -> bool:
        """
        Download a file from Google Drive

        Args:
            file_id: Google Drive file ID
            output_path: Where to save the file

        Returns:
            True if successful, False otherwise
        """
        # Google Drive direct download URL
        url = f"https://drive.google.com/uc?export=download&id={file_id}"

        try:
            session = requests.Session()
            response = session.get(url, stream=True)

            # Handle confirmation for large files
            if "download_warning" in response.cookies:
                # Get the confirmation token
                for key, value in response.cookies.items():
                    if key.startswith("download_warning"):
                        url = f"{url}&confirm={value}"
                        response = session.get(url, stream=True)
                        break

            response.raise_for_status()

            # Save the file
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            return True

        except requests.RequestException as e:
            print(f"Error downloading file from Google Drive: {e}")
            return False

    def _get_file_extension(self, file_id: str) -> str:
        """
        Try to get file extension from Google Drive metadata

        Args:
            file_id: Google Drive file ID

        Returns:
            File extension (with dot) or empty string
        """
        try:
            url = f"https://drive.google.com/file/d/{file_id}/view"
            response = requests.head(url, allow_redirects=True, timeout=5)

            # Try to get extension from Content-Type
            content_type = response.headers.get("Content-Type", "")

            if "video" in content_type:
                if "mp4" in content_type:
                    return ".mp4"
                elif "webm" in content_type:
                    return ".webm"
                elif "quicktime" in content_type or "mov" in content_type:
                    return ".mov"
                return ".mp4"  # Default for video
            elif "image" in content_type:
                if "jpeg" in content_type or "jpg" in content_type:
                    return ".jpg"
                elif "png" in content_type:
                    return ".png"
                elif "gif" in content_type:
                    return ".gif"
                elif "webp" in content_type:
                    return ".webp"
                return ".jpg"  # Default for image
            elif "audio" in content_type:
                if "mpeg" in content_type or "mp3" in content_type:
                    return ".mp3"
                elif "wav" in content_type:
                    return ".wav"
                return ".mp3"  # Default for audio

        except Exception:
            pass

        return ""

    def fetch(self, url: str, filename: Optional[str] = None) -> Optional[Path]:
        """
        Fetch a file from Google Drive, using cache if available

        Args:
            url: Google Drive URL
            filename: Optional filename to save as (auto-detected if not provided)

        Returns:
            Path to the local file or None if fetch failed
        """
        if not self.is_gdrive_link(url):
            raise ValueError(f"Not a valid Google Drive link: {url}")

        file_id = self.extract_file_id(url)
        if not file_id:
            raise ValueError(f"Could not extract file ID from URL: {url}")

        cache_key = self._get_cache_key(file_id)

        # Check if we have a valid cached version
        cached_path = self._get_cached_path(cache_key)
        if cached_path:
            print(f"Using cached file: {cached_path}")
            return cached_path

        # Determine filename
        if not filename:
            extension = self._get_file_extension(file_id)
            filename = f"{file_id}{extension}"

        output_path = self.cache_dir / filename

        # Download the file
        print(f"Downloading from Google Drive: {file_id}")
        if not self._download_file(file_id, output_path):
            return None

        # Update metadata
        self.metadata[cache_key] = {
            "file_id": file_id,
            "path": str(output_path),
            "timestamp": time.time(),
            "url": url,
        }
        self._save_metadata()

        print(f"Downloaded to: {output_path}")
        return output_path

    def clear_cache(self, older_than: Optional[int] = None):
        """
        Clear cached files

        Args:
            older_than: Only clear files older than this many seconds (None = clear all)
        """
        current_time = time.time()
        to_remove = []

        for cache_key, metadata in self.metadata.items():
            cached_time = metadata.get("timestamp", 0)
            age = current_time - cached_time

            if older_than is None or age > older_than:
                # Delete the file
                cached_path = Path(metadata.get("path", ""))
                if cached_path.exists():
                    try:
                        cached_path.unlink()
                        print(f"Deleted cached file: {cached_path}")
                    except OSError as e:
                        print(f"Warning: Could not delete {cached_path}: {e}")

                to_remove.append(cache_key)

        # Remove from metadata
        for cache_key in to_remove:
            del self.metadata[cache_key]

        self._save_metadata()
        print(f"Cleared {len(to_remove)} cached file(s)")


# Convenience functions
def fetch_from_gdrive(
    url: str, cache_dir: str = None, cache_duration: int = 86400
) -> Optional[Path]:
    """
    Convenience function to fetch a file from Google Drive

    Args:
        url: Google Drive URL
        cache_dir: Cache directory (default: ./gdrive_cache)
        cache_duration: Cache duration in seconds (default: 86400 = 24 hours)

    Returns:
        Path to local file or None if fetch failed
    """
    fetcher = GDriveFetcher(cache_dir=cache_dir, cache_duration=cache_duration)
    return fetcher.fetch(url)


def is_gdrive_link(url: str) -> bool:
    """
    Check if a URL is a Google Drive link

    Args:
        url: URL to check

    Returns:
        True if it's a Google Drive link
    """
    fetcher = GDriveFetcher()
    return fetcher.is_gdrive_link(url)


if __name__ == "__main__":
    # Example usage
    fetcher = GDriveFetcher(cache_duration=3600)  # 1 hour cache

    # Test URL detection
    test_urls = [
        "https://drive.google.com/file/d/1ABC123xyz/view",
        "https://drive.google.com/open?id=1ABC123xyz",
        "not_a_drive_link.mp4",
    ]

    for url in test_urls:
        print(f"Is '{url}' a Drive link? {fetcher.is_gdrive_link(url)}")
        if fetcher.is_gdrive_link(url):
            file_id = fetcher.extract_file_id(url)
            print(f"  File ID: {file_id}")
