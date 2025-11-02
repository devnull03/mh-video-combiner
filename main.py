"""
MoviePy Video Composite Script
Loads videos from TOML config and composites them side-by-side with text overlays
"""

import sys
from pathlib import Path

from moviepy import (
    ColorClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
)

from config_parser import create_example_config, load_config


def find_system_font():
    """Find a working system font"""
    # Common font paths on Linux
    possible_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        # Windows fonts
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        # Mac fonts
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]

    for font in possible_fonts:
        if Path(font).exists():
            return font

    # If no font found, return None and we'll use default
    return None


def load_and_analyze_clips(config):
    """
    Load all video clips and analyze their dimensions

    Returns:
        tuple: (clips, max_height, total_width, max_duration, fps)
    """
    print(f"\nLoading {len(config.videos)} video(s)...")

    clips = []
    max_height = 0
    total_width = 0
    max_duration = 0
    fps = None

    for idx, video_config in enumerate(config.videos):
        print(f"  [{idx + 1}] Loading: {video_config.path}")
        clip = VideoFileClip(str(video_config.path))

        # Track dimensions
        width, height = clip.size
        max_height = max(max_height, height)
        total_width += width
        max_duration = max(max_duration, clip.duration)

        # Get FPS from first video
        if fps is None:
            fps = clip.fps

        print(
            f"      Size: {width}x{height}, Duration: {clip.duration:.2f}s, FPS: {clip.fps}"
        )

        clips.append(clip)

    print(f"\n  Max height: {max_height}px")
    print(f"  Total width: {total_width}px")
    print(f"  Max duration: {max_duration:.2f}s")
    print(f"  Using FPS: {fps}")

    return clips, max_height, total_width, max_duration, fps


def create_text_overlay(text, font_size, width, font_path=None):
    """
    Create a text clip

    Args:
        text: Text to display
        font_size: Font size
        width: Width to center within
        font_path: Path to font file (optional)

    Returns:
        TextClip object
    """
    if not text:
        return None

    try:
        txt = TextClip(
            font=font_path,
            text=text,
            font_size=font_size,
            color="white",
            method="label",
            text_align="center",
            horizontal_align="center",
            vertical_align="bottom",
        )
    except Exception as e:
        print(f"    Warning: Could not create text '{text}': {e}")
        return None

    return txt


def create_composite_video(config):
    """
    Main function to create the composite video

    Args:
        config: CompositeConfig object with all settings
    """
    # Step 1: Load and analyze clips
    clips, max_height, total_width, max_duration, detected_fps = load_and_analyze_clips(
        config
    )

    # Use detected FPS from videos, or fall back to config
    output_fps = detected_fps if detected_fps else config.output_fps

    # Step 2: Normalize clip heights (no trimming - keep full duration)
    print("\nNormalizing clips...")
    normalized_clips = []

    for idx, clip in enumerate(clips):
        # Resize to match max height (maintaining aspect ratio)
        if clip.h != max_height:
            resized = clip.resized(height=max_height)
        else:
            resized = clip

        # If clip is shorter than max duration, extend with black background
        if resized.duration < max_duration:
            # Create black background for the remaining time
            black_bg = ColorClip(
                size=resized.size,
                color=(0, 0, 0),
                duration=max_duration - resized.duration,
            )
            # Concatenate original clip with black background
            from moviepy import concatenate_videoclips

            resized = concatenate_videoclips([resized, black_bg])
            print(
                f"  [{idx + 1}] Normalized to {resized.w}x{resized.h}, extended to {max_duration:.2f}s"
            )
        else:
            print(f"  [{idx + 1}] Normalized to {resized.w}x{resized.h}")

        normalized_clips.append(resized)

    # Recalculate total width after normalization
    total_width = sum(clip.w for clip in normalized_clips)

    # Step 3: Canvas is just the video area (text will overlay on bottom)
    canvas_height = max_height

    print(f"\nCanvas size: {total_width}x{canvas_height}")

    # Step 4: Position clips side by side
    print("\nPositioning clips...")
    positioned_clips = []
    current_x = 0

    for idx, clip in enumerate(normalized_clips):
        positioned = clip.with_position((current_x, 0))
        positioned_clips.append(positioned)
        print(f"  [{idx + 1}] Positioned at x={current_x}")
        current_x += clip.w

    # Step 5: Create text overlays for each video (overlaid on bottom of video)
    print("\nCreating text overlays...")
    font_path = find_system_font()
    if font_path:
        print(f"  Using font: {font_path}")
    else:
        print("  Using default font")

    text_clips = []
    current_x = 0

    for idx, (clip, video_config) in enumerate(zip(normalized_clips, config.videos)):
        clip_width = clip.w

        # Calculate total text height needed
        total_text_height = 0
        heading_clip = None
        subheading_clip = None

        if video_config.heading:
            heading_clip = create_text_overlay(
                video_config.heading, config.heading_font_size, clip_width, font_path
            )
            if heading_clip:
                total_text_height += heading_clip.h

        # Calculate spacing between heading and subheading based on font sizes
        spacing_between = int(
            config.heading_font_size * 0.5
        )  # 50% of heading font size

        if video_config.subheading:
            subheading_clip = create_text_overlay(
                video_config.subheading,
                config.subheading_font_size,
                clip_width,
                font_path,
            )
            if subheading_clip:
                total_text_height += subheading_clip.h + spacing_between

        # Create background for text area (semi-transparent) - sized to fit text
        if total_text_height > 0:
            # Calculate padding based on heading font size (30% top and bottom)
            vertical_padding = int(config.heading_font_size * 0.6)
            text_bg_height = total_text_height + vertical_padding
            text_bg = ColorClip(
                size=(clip_width, text_bg_height),
                color=config.text_bg_color,
                duration=max_duration,
            )
            text_bg = text_bg.with_opacity(config.text_bg_opacity)
            # Position at bottom of video
            text_bg_y = max_height - text_bg_height
            text_bg = text_bg.with_position((current_x, text_bg_y))
            text_clips.append(text_bg)

            # Position heading text with dynamic padding
            top_padding = int(
                config.heading_font_size * 0.3
            )  # 30% of heading font size
            text_y_offset = text_bg_y + top_padding
            if heading_clip:
                heading_x = current_x + (clip_width - heading_clip.w) // 2
                heading_clip = heading_clip.with_position((heading_x, text_y_offset))
                heading_clip = heading_clip.with_duration(max_duration)
                text_clips.append(heading_clip)
                text_y_offset += heading_clip.h + spacing_between

            # Position subheading text
            if subheading_clip:
                subheading_x = current_x + (clip_width - subheading_clip.w) // 2
                subheading_clip = subheading_clip.with_position(
                    (subheading_x, text_y_offset)
                )
                subheading_clip = subheading_clip.with_duration(max_duration)
                text_clips.append(subheading_clip)

        print(f"  [{idx + 1}] Text overlay created for '{video_config.heading}'")
        current_x += clip_width

    # Step 6: Composite everything together
    print("\nCompositing final video...")
    all_clips = positioned_clips + text_clips
    final = CompositeVideoClip(all_clips, size=(total_width, canvas_height))

    # Step 7: Export
    print(f"\nExporting to: {config.output_path}")
    print(f"Output FPS: {output_fps}")
    print("This may take a while...")

    final.write_videofile(
        config.output_path,
        fps=output_fps,
        codec="libx264",
        audio=False,  # Ignore audio
        preset=config.output_preset,  # Encoding speed preset
        threads=config.output_threads,  # Number of CPU threads
        bitrate=config.output_bitrate,  # Video bitrate
    )

    print(f"\n✓ Video composite saved to: {config.output_path}")

    # Step 8: Cleanup
    print("\nCleaning up...")
    final.close()
    for clip in clips:
        clip.close()

    print("✓ Done!")


def main():
    print("=" * 70)
    print("MoviePy Video Composite Script")
    print("=" * 70)

    # Check if config file is provided
    if len(sys.argv) < 2:
        print("\nNo configuration file provided.")
        print("Creating example configuration file...")
        create_example_config()
        print("\nUsage:")
        print("  python main.py <config.toml>")
        print("\nExample:")
        print("  python main.py example_config.toml")
        return

    config_path = sys.argv[1]

    try:
        # Load configuration
        print(f"\nLoading configuration from: {config_path}")
        config = load_config(config_path)
        print(f"✓ Configuration loaded: {len(config.videos)} video(s)")

        # Create composite
        create_composite_video(config)

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("\nTip: Create a config file first:")
        print(
            "  python -c 'from config_parser import create_example_config; create_example_config()'"
        )
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
