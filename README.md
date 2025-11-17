# Video Composite Tool

A pure ffmpeg-based tool for compositing multiple videos side-by-side with text overlays (headings and subheadings).

## Features

- **Side-by-side video composition**: Automatically arranges multiple videos horizontally
- **Dynamic canvas sizing**: Canvas size adapts to the combined width and height of all videos
- **Text overlays**: Add customizable headings and subheadings to each video
- **TOML configuration**: Simple configuration file format
- **Automatic normalization**: Videos are automatically resized to match heights and extended to longest duration
- **Pure ffmpeg**: Ultra-fast processing using ffmpeg directly (via ffmpeg-python library)
- **Dynamic spacing**: Text spacing automatically scales with font size
- **Google Drive support**: Automatically download and cache files from Google Drive links
- **Smart directory detection**: Pass a directory name and it automatically finds the matching .toml file

## Requirements

- Python 3.12+
- **ffmpeg** (must be installed separately - this is the actual video processor)
- ffmpeg-python 0.2.0+ (Python wrapper - installed automatically)
- requests 2.31.0+ (for Google Drive downloads - installed automatically)

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
pip install ffmpeg-python requests
```

**Note**: The script uses Python's built-in `tomllib` (available in Python 3.11+) for TOML parsing.

## Performance

This tool uses **pure ffmpeg** for maximum speed:

- ✅ **10-50x faster** than Python frame-by-frame processing
- ✅ Native ffmpeg filters (no Python overhead)
- ✅ Multi-threaded encoding (default: 4 threads)
- ✅ No audio processing (faster encoding)
- ✅ GPU acceleration support (if ffmpeg built with it)

**Example**: Compositing 4 videos (9 seconds each) takes ~10-15 seconds

### Default Optimizations
- **Preset**: `ultrafast` - Fastest encoding speed
- **Threads**: `4` - Uses multiple CPU cores
- **Bitrate**: `5000k` - Balanced quality/size
- **Audio**: Disabled - No audio processing
- **FPS**: Auto-detected from source videos

## Usage

### Basic Usage

**Method 1: Using config file directly**
```bash
python main.py config.toml
```

**Method 2: Using directory name (auto-finds matching .toml)**
```bash
python main.py vid2  # Automatically looks for vid2.toml
```

### 1. Create a Configuration File

Run the script without arguments to generate an example config:

```bash
python main.py
```

This creates `example_config.toml`:

```toml
# Output settings
[output]
path = "output_composite.mp4"
# fps = 24  # Optional: Auto-detected from input videos by default
preset = "ultrafast"  # Encoding speed preset
threads = 4  # Number of CPU threads
bitrate = "5000k"  # Video bitrate

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
# Supports local files and Google Drive links!
[[videos]]
path = "video1.mp4"
# path = "https://drive.google.com/file/d/YOUR_FILE_ID/view"  # Google Drive links work!
heading = "First Video"
subheading = "Description for first video"

[[videos]]
path = "video2.mp4"
heading = "Second Video"
subheading = "Description for second video"
```

### 2. Edit the Configuration

Modify the config file with your actual video paths:

```toml
[output]
path = "my_composite.mp4"

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

**Using config file:**
```bash
python main.py my_config.toml
```

**Using directory (auto-detects .toml file):**
```bash
# If you have a directory structure like:
# my_project/
# my_project.toml

python main.py my_project  # Automatically uses my_project.toml
```

### Google Drive Support

You can use Google Drive links directly in your config files! Files are automatically downloaded and cached.

```toml
[[videos]]
path = "https://drive.google.com/file/d/1ABC123xyz/view"
heading = "Video from Drive"
subheading = "Auto-downloaded and cached"

[[videos]]
path = "local_video.mp4"  # Mix Drive and local files!
heading = "Local Video"
```

**Supported Google Drive URL formats:**
- `https://drive.google.com/file/d/FILE_ID/view`
- `https://drive.google.com/open?id=FILE_ID`
- `https://docs.google.com/document/d/FILE_ID/edit`

**Caching:**
- Files are cached in `./gdrive_cache/` by default
- Cache duration: 24 hours (configurable)
- Re-runs use cached files (no re-download)
- Cache automatically expires and re-downloads after 24 hours

## How It Works

1. **Load Videos**: All videos specified in the config are analyzed using ffprobe
2. **Analyze Dimensions**: Determines maximum height, total width, and longest duration
3. **Build Filter Chain**: Creates ffmpeg filter pipeline for:
   - Scaling videos to same height (maintaining aspect ratio)
   - Padding shorter videos with black frames to match longest duration
   - Adding semi-transparent text background boxes
   - Overlaying heading and subheading text
   - Stacking videos horizontally
4. **Execute ffmpeg**: Runs single ffmpeg command with complete filter chain
5. **Export**: Outputs final composite video

All processing happens in **native ffmpeg** - no Python frame processing!

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
- `path`: Path to the video file or Google Drive URL (required)
- `heading`: Main text overlay (optional)
- `subheading`: Secondary text overlay (optional)

**Note:** Google Drive links are automatically detected and downloaded with caching.

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
threads = 8  # Use more CPU cores

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

## Troubleshooting

### FFmpeg Not Found

```
✗ Error: ffmpeg not found
```

Install ffmpeg (see Requirements section above). Make sure `ffmpeg` command works in your terminal.

### Video Not Found

Ensure all video paths in your config file are correct. Use absolute paths if relative paths aren't working:

```toml
[[videos]]
path = "/home/user/videos/video1.mp4"  # Absolute path
```

Or use Google Drive links:

```toml
[[videos]]
path = "https://drive.google.com/file/d/YOUR_FILE_ID/view"
```

### Google Drive Download Fails

If Google Drive downloads fail:
- Check the file permissions (must be publicly accessible or "Anyone with the link")
- Verify the URL format is correct
- Check your internet connection
- Try clearing the cache: delete the `./gdrive_cache/` directory

### Memory Issues

For very large videos or many videos, consider:
- Reducing the resolution of source videos first
- Lowering the output FPS
- Processing fewer videos at once

### Slow Encoding

**Quick fixes:**
- ✅ Already using `preset = "ultrafast"` by default
- Increase `threads` to match your CPU cores (check with `nproc` on Linux/Mac)
- Lower the `bitrate` (e.g., "2000k" or "3000k")
- Test with short video clips first

**For better quality (slower):**
- Use `preset = "medium"` or `"slow"`
- Increase `bitrate` (e.g., "10000k" or higher)

**Still too slow?**
- Pre-process videos: resize to lower resolution, trim unnecessary portions
- Use faster storage (SSD instead of HDD)
- Check CPU usage - should be near 100% when encoding

### Text Not Showing / Text Issues

The script uses ffmpeg's `drawtext` filter which requires:
- Text special characters like `:` and `'` are automatically escaped
- Text is centered horizontally within each video
- Text is positioned at the bottom with dynamic padding

If text isn't showing up, check ffmpeg was compiled with `--enable-libfreetype`:
```bash
ffmpeg -filters | grep drawtext
```

## Performance Tips

### Speed Comparison

**Encoding presets** (from fastest to slowest):
- `ultrafast` - ~10-15 seconds (default)
- `veryfast` - ~30-45 seconds
- `medium` - ~2-3 minutes
- `slow` - ~5-10 minutes

### Workflow Recommendation

1. **Quick preview** with `preset = "ultrafast"` to check layout
2. **Final export** with `preset = "medium"` or `"slow"` for quality

### Hardware Recommendations

**Minimum**:
- CPU: 4 cores
- RAM: 8 GB
- Storage: HDD with 50 GB free

**Recommended**:
- CPU: 8+ cores
- RAM: 16 GB
- Storage: SSD with 100 GB free

**Optimal**:
- CPU: 12+ cores
- RAM: 32 GB
- Storage: NVMe SSD

## Project Structure

```
video_composite/
├── main.py              # Main script (uses ffmpeg-python)
├── config_parser.py     # TOML configuration parser
├── gdrive_fetcher.py    # Google Drive downloader with caching
├── example_config.toml  # Example configuration
├── pyproject.toml       # Python dependencies
├── gdrive_cache/        # Cached Google Drive files (auto-created)
└── README.md            # This file
```

## Technical Details

### Why ffmpeg-python?

This tool uses the `ffmpeg-python` library which provides:
- Clean Python API for building ffmpeg commands
- Method chaining for filter operations
- Better error handling
- Same performance as raw ffmpeg (just a wrapper)

### Filter Chain

The script builds a complex ffmpeg filter chain:
```
[0:v] scale, tpad, drawbox, drawtext, drawtext [v0]
[1:v] scale, tpad, drawbox, drawtext, drawtext [v1]
[2:v] scale, tpad, drawbox, drawtext, drawtext [v2]
[v0][v1][v2] hstack=inputs=3 [out]
```

This runs entirely in ffmpeg's native C code for maximum performance.

## License

MIT