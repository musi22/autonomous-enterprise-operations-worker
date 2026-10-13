import os
import shutil
import cv2
import numpy as np
from PIL import Image, ImageSequence

def convert_webp_to_mp4():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    input_path = os.path.join(base_dir, "docs", "screenshots", "platform_demo_walkthrough.webp")
    output_path = os.path.join(base_dir, "docs", "screenshots", "platform_demo_walkthrough.mp4")
    
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads", "platform_demo_walkthrough.mp4")
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "platform_demo_walkthrough.mp4")

    print(f"Reading animated WebP from: {input_path}")
    im = Image.open(input_path)
    frames = []
    durations = []

    for idx, frame in enumerate(ImageSequence.Iterator(im)):
        rgb_frame = frame.convert('RGB')
        np_frame = np.array(rgb_frame)
        bgr_frame = cv2.cvtColor(np_frame, cv2.COLOR_RGB2BGR)
        frames.append(bgr_frame)
        durations.append(frame.info.get('duration', 100))

    total_frames = len(frames)
    print(f"Extracted {total_frames} frames.")

    avg_duration = sum(durations) / len(durations) if durations else 100
    fps = max(1, round(1000.0 / avg_duration)) if avg_duration > 0 else 10
    print(f"Calculated FPS: {fps}")

    h, w, _ = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    for f in frames:
        out.write(f)
    out.release()

    print(f"Successfully generated MP4 video: {output_path} ({os.path.getsize(output_path)} bytes)")

    # Copy to Downloads and Desktop
    shutil.copy2(output_path, downloads_path)
    print(f"Copied to Downloads: {downloads_path}")

    shutil.copy2(output_path, desktop_path)
    print(f"Copied to Desktop: {desktop_path}")

if __name__ == "__main__":
    convert_webp_to_mp4()
