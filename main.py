import instaloader
import os
import subprocess

# ==============================
# CONFIGURATION
# ==============================

profile_url = input("Instagram profile URL: ").strip()

username = profile_url.rstrip("/").split("/")[-1]

download_folder = f"downloads/{username}/original"
converted_folder = f"downloads/{username}/60fps"

os.makedirs(download_folder, exist_ok=True)
os.makedirs(converted_folder, exist_ok=True)

TARGET_FPS = 60

# ==============================
# INSTAGRAM DOWNLOADER
# ==============================

loader = instaloader.Instaloader(
    dirname_pattern=download_folder,
    filename_pattern="{date_utc}",
    download_pictures=False,
    download_videos=True,
    download_video_thumbnails=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False
)

# ==============================
# VIDEO INFORMATION
# ==============================

def get_video_info(video_path):

    command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate",
        "-of", "default=noprint_wrappers=1",
        video_path
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    info = {}

    for line in result.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            info[key] = value

    fps = eval(info.get("avg_frame_rate", "0/1"))

    return info.get("width"), info.get("height"), float(fps)


# ==============================
# CONVERT TO 60 FPS
# ==============================

def convert_to_60fps(video_path):

    filename = os.path.basename(video_path)

    output_path = os.path.join(
        converted_folder,
        filename
    )

    try:

        width, height, fps = get_video_info(video_path)

        print(f"\nVideo: {filename}")
        print(f"Resolution: {width}x{height}")
        print(f"Original FPS: {fps}")

        if fps >= TARGET_FPS:

            print("Already 60 FPS or higher. Keeping original.")

            return

        command = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vf", f"minterpolate=fps={TARGET_FPS}",
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "medium",
            "-c:a", "copy",
            output_path
        ]

        subprocess.run(command, check=True)

        print(f"Converted successfully: {output_path}")

    except Exception as e:

        print(f"Conversion error: {e}")


# ==============================
# DOWNLOAD ALL VIDEOS
# ==============================

try:

    profile = instaloader.Profile.from_username(
        loader.context,
        username
    )

    video_count = 0

    for post in profile.get_posts():

        if post.is_video:

            print(f"\nDownloading: {post.date_utc}")

            loader.download_post(
                post,
                target=username
            )

            video_count += 1

    print(f"\nDownloaded posts: {video_count}")

    # ==============================
    # PROCESS DOWNLOADED VIDEOS
    # ==============================

    print("\nStarting FPS processing...")

    for filename in os.listdir(download_folder):

        if filename.lower().endswith((".mp4", ".mov", ".mkv")):

            video_path = os.path.join(
                download_folder,
                filename
            )

            convert_to_60fps(video_path)

    print("\nAll tasks completed!")

    print(f"Original videos: {download_folder}")
    print(f"60 FPS videos: {converted_folder}")

except Exception as e:

    print(f"\nError: {e}")
