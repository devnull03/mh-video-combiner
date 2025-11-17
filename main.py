"""
FFmpeg Video Composite Script
Uses ffmpeg-python library for clean, fast video processing
"""

import sys
from pathlib import Path

import ffmpeg

from config_parser import create_example_config, load_config


def get_video_info(video_path: str) -> dict:
    """Get video information using ffmpeg.probe"""
    try:
        probe = ffmpeg.probe(str(video_path))
    except ffmpeg.Error as e:
        raise RuntimeError(f"Failed to probe {video_path}: {e.stderr.decode()}")
    except FileNotFoundError:
        raise RuntimeError(
            "ffmpeg/ffprobe not found. Please install ffmpeg: https://ffmpeg.org/download.html"
        )

    # Get video stream
    video_stream = next(
        (s for s in probe["streams"] if s["codec_type"] == "video"), None
    )
    if not video_stream:
        raise RuntimeError(f"No video stream found in {video_path}")

    # Parse frame rate
    fps_str = video_stream.get("r_frame_rate", "30/1")
    num, den = map(int, fps_str.split("/"))
    fps = num / den if den != 0 else 30

    # Get duration
    duration = float(
        video_stream.get("duration") or probe.get("format", {}).get("duration", 0)
    )

    # Calculate frame count
    # Try to get from nb_frames first (most accurate if available)
    frame_count = video_stream.get("nb_frames")
    if frame_count:
        frame_count = int(frame_count)
    else:
        # Calculate from duration and fps
        frame_count = int(duration * fps)

    return {
        "width": int(video_stream["width"]),
        "height": int(video_stream["height"]),
        "fps": fps,
        "duration": duration,
        "frame_count": frame_count,
    }


def create_composite_video(config):
    """
    Create side-by-side video composite with text overlays using ffmpeg-python

    Args:
        config: CompositeConfig object with all settings
    """
    print("\n" + "=" * 70)
    print("FFmpeg Video Composite")
    print("=" * 70)

    # Step 1: Analyze all videos
    print(f"\nAnalyzing {len(config.videos)} video(s)...")

    video_infos = []
    for idx, video_config in enumerate(config.videos):
        print(f"  [{idx + 1}] Loading: {video_config.path}")
        info = get_video_info(str(video_config.path))

        # Use manual override if provided, otherwise use detected frame count
        if video_config.frame_count_override is not None:
            info["frame_count"] = video_config.frame_count_override
            frame_count_suffix = " (manual override)"
        else:
            frame_count_suffix = ""

        video_infos.append(info)
        if config.show_frame_count:
            print(
                f"      Size: {info['width']}x{info['height']}, "
                f"Duration: {info['duration']:.2f}s, FPS: {info['fps']:.1f}, "
                f"Frames: {info['frame_count']}{frame_count_suffix}"
            )
        else:
            print(
                f"      Size: {info['width']}x{info['height']}, "
                f"Duration: {info['duration']:.2f}s, FPS: {info['fps']:.1f}"
            )

    # Find max dimensions and duration
    max_height = max(info["height"] for info in video_infos)
    max_duration = max(info["duration"] for info in video_infos)
    fps = video_infos[0]["fps"]  # Use first video's FPS
    output_fps = config.output_fps if config.output_fps else fps

    print(f"\n  Max height: {max_height}px")
    print(f"  Max duration: {max_duration:.2f}s")
    print(f"  Output FPS: {output_fps:.1f}")

    # Step 2: Build ffmpeg filter chain
    print("\nBuilding filter chain...")

    # Create input streams
    input_streams = []
    for video_config in config.videos:
        input_streams.append(ffmpeg.input(str(video_config.path)))

    # Process each video stream
    processed_streams = []
    for i, (stream, video_config, info) in enumerate(
        zip(input_streams, config.videos, video_infos)
    ):
        # Get video stream
        v = stream.video

        # Scale to max height
        v = v.filter("scale", -2, max_height)

        # Pad video to max duration if needed
        if info["duration"] < max_duration:
            pad_duration = max_duration - info["duration"]
            v = v.filter("tpad", stop_mode="clone", stop_duration=pad_duration)

        # Calculate dynamic spacing based on font size
        spacing_between = int(config.heading_font_size * 0.5)
        vertical_padding = int(config.heading_font_size * 0.6)
        top_padding = int(config.heading_font_size * 0.3)

        # Add semi-transparent background box for text
        if video_config.heading or video_config.subheading:
            box_height = (
                config.heading_font_size
                + spacing_between
                + config.subheading_font_size
                + vertical_padding
            )

            v = v.filter(
                "drawbox",
                x=0,
                y=f"h-{box_height}",
                color=f"black@{config.text_bg_opacity}",
                width="iw",
                height=box_height,
                t="fill",
            )

        # Add heading text
        if video_config.heading:
            box_height = (
                config.heading_font_size
                + spacing_between
                + config.subheading_font_size
                + vertical_padding
            )

            heading_text = video_config.heading.replace(":", r"\:").replace(
                "'", r"'\''"
            )
            v = v.filter(
                "drawtext",
                text=heading_text,
                fontsize=config.heading_font_size,
                fontcolor=config.text_color,
                x="(w-text_w)/2",
                y=f"h-{box_height}+{top_padding}",
            )

        # Add subheading text
        if video_config.subheading:
            subheading_text = video_config.subheading.replace(":", r"\:").replace(
                "'", r"'\''"
            )
            subheading_y = max_height - vertical_padding - config.subheading_font_size
            v = v.filter(
                "drawtext",
                text=subheading_text,
                fontsize=config.subheading_font_size,
                fontcolor=config.text_color,
                x="(w-text_w)/2",
                y=subheading_y,
            )

        # Add frame count overlay in top-left corner
        if config.show_frame_count:
            # Get frame count (use override if provided)
            if video_config.frame_count_override is not None:
                frame_count = video_config.frame_count_override
            else:
                frame_count = info["frame_count"]

            # Calculate box dimensions for frame count
            frame_count_padding = 10
            frame_count_box_width = int(
                config.frame_count_font_size * 4
            )  # Approximate width
            frame_count_box_height = int(config.frame_count_font_size * 1.5)

            # Add background box for frame count
            v = v.filter(
                "drawbox",
                x=0,
                y=0,
                color=f"black@{config.text_bg_opacity}",
                width=frame_count_box_width,
                height=frame_count_box_height,
                t="fill",
            )

            # Add frame count text
            frame_count_text = f"Frames: {frame_count}"
            v = v.filter(
                "drawtext",
                text=frame_count_text,
                fontsize=config.frame_count_font_size,
                fontcolor=config.text_color,
                x=frame_count_padding,
                y=frame_count_padding,
            )

        processed_streams.append(v)

    # Horizontal stack all videos
    print(f"  Stacking {len(processed_streams)} videos horizontally...")
    stacked = ffmpeg.filter(processed_streams, "hstack", inputs=len(processed_streams))

    # Step 3: Get audio from first video
    print("\nAdding audio from first video...")
    first_audio = input_streams[0].audio

    # Step 4: Output with encoding settings
    print("\nEncoding video with ffmpeg...")
    print(f"  Preset: {config.output_preset}")
    print(f"  Threads: {config.output_threads}")
    print(f"  Bitrate: {config.output_bitrate}")
    print(f"\nExporting to: {config.output_path}")
    print("Encoding...\n")

    try:
        output = ffmpeg.output(
            stacked,
            first_audio,
            str(config.output_path),
            r=output_fps,
            vcodec="libx264",
            acodec="aac",
            audio_bitrate="192k",
            preset=config.output_preset,
            video_bitrate=config.output_bitrate,
            threads=config.output_threads,
        )

        # Run with error stats
        ffmpeg.run(output, overwrite_output=True, quiet=False)

        print(f"\n✓ Video composite saved to: {config.output_path}")
        print("✓ Audio from first video included")
        print("\n✓ Done!")

    except ffmpeg.Error as e:
        print("\n✗ FFmpeg encoding failed:")
        print(e.stderr.decode() if e.stderr else str(e))
        raise
    except FileNotFoundError:
        print("\n✗ Error: ffmpeg not found")
        print("Please install ffmpeg: https://ffmpeg.org/download.html")
        sys.exit(1)


def main():
    print("=" * 70)
    print("FFmpeg Video Composite Script (Ultra-Fast)")
    print("=" * 70)

    # Check if config file is provided
    if len(sys.argv) < 2:
        print("\nNo configuration file provided.")
        print("Creating example configuration file...")
        create_example_config()
        print("\nUsage:")
        print("  python main.py <config.toml>")
        print("  python main.py <directory>  # Looks for directory.toml")
        print("\nExample:")
        print("  python main.py example_config.toml")
        print("  python main.py vid2  # Looks for vid2.toml")
        return

    input_path = sys.argv[1]
    input_path_obj = Path(input_path)

    # Check if input is a directory
    if input_path_obj.is_dir():
        # Look for a .toml file with the same name as the directory
        dir_name = input_path_obj.name
        config_path = input_path_obj.parent / f"{dir_name}.toml"

        if not config_path.exists():
            print(
                f"\n✗ Error: Directory provided but config file not found: {config_path}"
            )
            print(f"\nWhen passing a directory, expected to find: {dir_name}.toml")
            print(f"in the same location as the directory.")
            sys.exit(1)

        print(f"\n✓ Found config file for directory: {config_path}")
        config_path = str(config_path)
    else:
        config_path = input_path

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
        print("  python main.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
