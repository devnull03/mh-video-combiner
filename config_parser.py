"""
TOML Configuration Parser for Video Composite
Handles loading and validating TOML configuration files
"""

import tomllib
from pathlib import Path
from typing import Any, Dict, List


class VideoConfig:
    """Represents configuration for a single video"""

    def __init__(self, path: str, heading: str = "", subheading: str = ""):
        self.path = Path(path)
        self.heading = heading
        self.subheading = subheading

    def validate(self) -> bool:
        """Validate that the video file exists"""
        if not self.path.exists():
            raise FileNotFoundError(f"Video file not found: {self.path}")
        return True

    def __repr__(self):
        return f"VideoConfig(path={self.path}, heading='{self.heading}', subheading='{self.subheading}')"


class CompositeConfig:
    """Main configuration for the video composite"""

    def __init__(self, config_dict: Dict[str, Any]):
        self.videos: List[VideoConfig] = []
        output_config = config_dict.get("output", {})
        self.output_path = output_config.get("path", "output_composite.mp4")
        self.output_fps = output_config.get(
            "fps", None
        )  # None = auto-detect from videos
        self.output_preset = output_config.get("preset", "ultrafast")
        self.output_threads = output_config.get("threads", 4)
        self.output_bitrate = output_config.get("bitrate", "5000k")

        # Text styling
        text_config = config_dict.get("text", {})
        self.heading_font_size = text_config.get("heading_font_size", 60)
        self.subheading_font_size = text_config.get("subheading_font_size", 36)
        self.text_color = text_config.get("color", "white")
        self.text_bg_color = tuple(text_config.get("bg_color", [0, 0, 0]))
        self.text_bg_opacity = text_config.get("bg_opacity", 0.7)

        # Parse videos
        videos_list = config_dict.get("videos", [])
        for video_data in videos_list:
            video = VideoConfig(
                path=video_data.get("path", ""),
                heading=video_data.get("heading", ""),
                subheading=video_data.get("subheading", ""),
            )
            self.videos.append(video)

    def validate(self) -> bool:
        """Validate all video configurations"""
        if not self.videos:
            raise ValueError("No videos specified in configuration")

        for video in self.videos:
            video.validate()

        return True

    def __repr__(self):
        return (
            f"CompositeConfig(videos={len(self.videos)}, output='{self.output_path}')"
        )


def load_config(config_path: str) -> CompositeConfig:
    """
    Load and parse a TOML configuration file

    Args:
        config_path: Path to the TOML configuration file

    Returns:
        CompositeConfig object with parsed configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Load TOML file
    with open(config_file, "rb") as f:
        config_dict = tomllib.load(f)

    # Parse and validate
    config = CompositeConfig(config_dict)
    config.validate()

    return config


def create_example_config(output_path: str = "example_config.toml"):
    """
    Create an example TOML configuration file

    Args:
        output_path: Where to save the example config
    """
    example_toml = """# Video Composite Configuration

# Output settings
[output]
path = "output_composite.mp4"
# fps = 24  # Optional: Leave unset to auto-detect from input videos
preset = "ultrafast"  # Encoding speed: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
threads = 4  # Number of CPU threads to use for encoding
bitrate = "5000k"  # Video bitrate (e.g., "5000k", "10000k" for higher quality)

# Text styling
[text]
heading_font_size = 60
subheading_font_size = 36
color = "white"
bg_color = [0, 0, 0]  # RGB values
bg_opacity = 0.7
# Note: Spacing and padding are automatically calculated based on font sizes
# Spacing between lines = 50% of heading_font_size
# Vertical padding = 60% of heading_font_size

# Videos to composite (side by side)
[[videos]]
path = "video1.mp4"
heading = "First Video"
subheading = "Description for first video"

[[videos]]
path = "video2.mp4"
heading = "Second Video"
subheading = "Description for second video"

[[videos]]
path = "video3.mp4"
heading = "Third Video"
subheading = "Description for third video"
"""

    with open(output_path, "w") as f:
        f.write(example_toml)

    print(f"Example configuration created at: {output_path}")


if __name__ == "__main__":
    # Create example config when run directly
    create_example_config()
    print("\nExample usage:")
    print("  from config_parser import load_config")
    print("  config = load_config('example_config.toml')")
    print("  for video in config.videos:")
    print("      print(video)")
