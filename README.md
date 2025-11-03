# Video Composite Tool

A MoviePy-based tool for compositing multiple videos side-by-side with text overlays (headings and subheadings).

## Features

- **Side-by-side video composition**: Automatically arranges multiple videos horizontally
- **Dynamic canvas sizing**: Canvas size adapts to the combined width and height of all videos
- **Text overlays**: Add customizable headings and subheadings to each video
- **TOML configuration**: Simple configuration file format
- **Automatic normalization**: Videos are automatically resized to match heights and trimmed to the shortest duration
- **Cross-platform font detection**: Automatically finds and uses system fonts

## Requirements

- Python 3.12+
- ffmpeg (must be installed separately)
- MoviePy 2.2.1+

### Installing ffmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

**macOS:**
```bash
brew install ffmpeg
```

## Installation

1. Install dependencies:
```bash
uv sync
# or if using pip:
pip install moviepy
```

**Note**: The script uses Python's built-in `tomllib` (available in Python 3.11+) for TOML parsing, so no additional TOML library is needed.

## Performance Optimization

Video encoding can be slow. The script includes several optimizations:

### Default Optimizations (Already Active)
- **Preset**: `ultrafast` - Fastest encoding speed
- **Threads**: `4` - Uses multiple CPU cores
- **Bitrate**: `5000k` - Balanced quality/size
- **Audio**: Disabled - No audio processing for faster encoding
- **Logging**: Disabled - Reduces I/O overhead
- **FPS**: Auto-detected from source videos

### Additional Speed Improvements
1. **Increase threads** to match your CPU cores (e.g., `threads = 8`)
2. **Lower bitrate** for faster encoding (e.g., `bitrate = "3000k"`)
3. **Use smaller source videos** - resize large 4K videos to 1080p first
4. **Test with short clips** before processing long videos

### Ultra-Fast Alternative (No Text Overlays)
For maximum speed without text overlays, see `ffmpeg_fallback.py` which uses direct ffmpeg commands and can be **10-50x faster** than MoviePy rendering.

## Usage

### 1. Create a Configuration File

Run the script without arguments to generate an example config:

```bash
uv run python main.py
```

This creates `example_config.toml` with the following structure:

```toml
# Video Composite Configuration

# Output settings
[output]
path = "output_composite.mp4"
# fps = 24  # Optional: Auto-detected from input videos by default
preset = "ultrafast"  # Encoding speed preset
threads = 4  # Number of CPU threads
bitrate = "5000k"  # Video bitrate

# Text styling
[text]
heading_font_size = 40
subheading_font_size = 24
color = "white"
bg_color = [0, 0, 0]  # RGB values [R, G, B]
bg_opacity = 0.7

# Videos to composite (side by side)
[[videos]]
path = "video1.mp4"
heading = "First Video"
subheading = "Description for first video"

[[videos]]
path = "video2.mp4"
heading = "Second Video"
subheading = "Description for second video"
```

### 2. Edit the Configuration

Modify the config file to point to your actual videos:

```toml
# Output settings
[output]
path = "my_composite.mp4"
# fps = 30  # Optional: Uncomment to override auto-detected FPS
preset = "medium"  # Better quality, slower encoding
threads = 8  # Use more threads if you have more CPU cores
bitrate = "10000k"  # Higher quality

# Text styling
[text]
heading_font_size = 50
subheading_font_size = 28
color = "white"
bg_color = [0, 0, 0]
bg_opacity = 0.8

[[videos]]
path = "/path/to/your/video1.mp4"
heading = "Camera 1"
subheading = "Front View"

[[videos]]
path = "/path/to/your/video2.mp4"
heading = "Camera 2"
subheading = "Side View"

[[videos]]
path = "/path/to/your/video3.mp4"
heading = "Camera 3"
subheading = "Top View"
```

### 3. Run the Composite

```bash
uv run python main.py my_config.toml
```

## How It Works

1. **Load Videos**: All videos specified in the config are loaded
2. **Analyze Dimensions**: The script determines the maximum height, total width, and longest duration
3. **Normalize**: Videos are resized to match the tallest video's height. Shorter videos are extended with black backgrounds to match the longest duration
4. **Create Canvas**: A canvas is generated with:
   - Width = sum of all video widths
   - Height = max video height
   - Duration = longest video duration
5. **Position Videos**: Videos are placed side-by-side horizontally
6. **Add Text**: Headings and subheadings are overlaid on a semi-transparent background at the bottom of each video
7. **Export**: The final composite is rendered to the output file

## Configuration Options

### Output Settings

- `path`: Output file path (default: "output_composite.mp4")
- `fps`: Frames per second for output video (optional, auto-detected from first input video)
  - Leave unset to use the FPS from your input videos
  - Set explicitly (e.g., `fps = 30`) to override
- `preset`: Encoding speed preset (default: "ultrafast")
  - Options: `ultrafast`, `superfast`, `veryfast`, `faster`, `fast`, `medium`, `slow`, `slower`, `veryslow`
  - Faster presets = quicker encoding but larger file size
  - Slower presets = better compression and quality but takes longer
- `threads`: Number of CPU threads to use (default: 4)
  - Set higher if you have more CPU cores (e.g., 8, 16)
- `bitrate`: Video bitrate for quality control (default: "5000k")
  - Higher = better quality but larger file (e.g., "10000k", "15000k")
  - Lower = faster encoding and smaller file (e.g., "2000k", "3000k")

### Text Styling

- `heading_font_size`: Font size for main heading (default: 60)
- `subheading_font_size`: Font size for subheading (default: 36)
- `color`: Text color (default: "white")
- `bg_color`: RGB values for text background, e.g., [255, 0, 0] for red (default: [0, 0, 0])
- `bg_opacity`: Opacity of text background, 0.0-1.0 (default: 0.7)

**Note**: Spacing and padding are automatically calculated based on `heading_font_size`:
- Spacing between heading and subheading = 50% of heading font size
- Vertical padding (top/bottom) = 60% of heading font size
- Top padding = 30% of heading font size

This means larger fonts automatically get more breathing room!

### Video Entries

Each `[[videos]]` section requires:
- `path`: Path to the video file (required)
- `heading`: Main text overlay (optional)
- `subheading`: Secondary text overlay (optional)

## Examples

### Two Videos Side-by-Side

```toml
[output]
path = "comparison.mp4"

[[videos]]
path = "before.mp4"
heading = "Before"

[[videos]]
path = "after.mp4"
heading = "After"
```

### Multi-Camera Setup

```toml
[output]
path = "multicam.mp4"
fps = 30

[text]
heading_font_size = 55
subheading_font_size = 32

[[videos]]
path = "cam1.mp4"
heading = "🎥 Front"
subheading = "Main View"

[[videos]]
path = "cam2.mp4"
heading = "🎥 Left"
subheading = "Side Angle"

[[videos]]
path = "cam3.mp4"
heading = "🎥 Right"
subheading = "Side Angle"

[[videos]]
path = "cam4.mp4"
heading = "🎥 Top"
subheading = "Overhead"
```

## Ultra-Fast Mode (Advanced)

If you need maximum speed and don't need text overlays, you can use the ffmpeg fallback:

```python
from ffmpeg_fallback import create_side_by_side_ffmpeg

create_side_by_side_ffmpeg(
    ["video1.mp4", "video2.mp4", "video3.mp4"],
    "output.mp4",
    preset="ultrafast",
    threads=8
)
```

**Trade-offs:**
- ✅ 10-50x faster than MoviePy
- ✅ Direct ffmpeg processing
- ❌ No text overlays
- ❌ No dynamic spacing

## Troubleshooting

### Font Errors

If you get font-related errors, the script will automatically try to find system fonts. On Linux, make sure you have DejaVu or Liberation fonts installed:

```bash
sudo apt install fonts-dejavu fonts-liberation
```

### Video Not Found

Ensure all video paths in your config file are correct. Use absolute paths if relative paths aren't working.

### Memory Issues

For very large videos or many videos, consider:
- Reducing the resolution of source videos first
- Lowering the output FPS
- Processing fewer videos at once

### Slow Encoding

**Quick fixes:**
- ✅ Already using `preset = "ultrafast"` by default
- ✅ Already disabled audio and logging
- Increase `threads` to match your CPU cores (e.g., 8, 16)
- Lower the `bitrate` (e.g., "2000k" or "3000k")
- Test with short video clips first

**For better quality (slower):**
- Use `preset = "medium"` or `"slow"`
- Increase `bitrate` (e.g., "10000k" or higher)

**Still too slow?**
- Consider using `ffmpeg_fallback.py` for ultra-fast processing (no text overlays)
- Pre-process videos: resize to lower resolution, trim unnecessary portions
- Process videos in smaller batches

## Project Structure

```
video_composite/
├── main.py              # Main script
├── config_parser.py     # TOML configuration parser
├── example_config.toml  # Example configuration
├── pyproject.toml       # Python dependencies
└── README.md            # This file
```

## License

MIT