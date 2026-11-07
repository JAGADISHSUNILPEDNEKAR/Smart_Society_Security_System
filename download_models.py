"""
Automated Model Downloader for Smart Society Security System.
Downloads and verifies YuNet and SFace ONNX models from the official OpenCV Model Zoo.
"""

import os
import urllib.request
import hashlib
import sys
from pathlib import Path

MODEL_METADATA = {
    "face_detection_yunet_2023mar.onnx": {
        "url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
        "sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
        "description": "YuNet Face Detector (OpenCV Model Zoo 2023mar)"
    },
    "face_recognition_sface_2021dec.onnx": {
        "url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
        "sha256": "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
        "description": "SFace 128-d Face Feature Extractor (OpenCV Model Zoo 2021dec)"
    }
}

def verify_file(filepath: Path, expected_sha256: str) -> bool:
    if not filepath.exists():
        return False
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower() == expected_sha256.lower()

def download_models(target_dir: str = "models", force: bool = False) -> bool:
    out_dir = Path(target_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    all_ok = True

    print(f"Ensuring deep learning models in '{out_dir}'...")
    for filename, meta in MODEL_METADATA.items():
        file_path = out_dir / filename
        if not force and verify_file(file_path, meta["sha256"]):
            print(f" [OK] {filename} is already present and valid.")
            continue

        print(f" [DOWNLOADING] {filename} ({meta['description']})...")
        try:
            urllib.request.urlretrieve(meta["url"], file_path)
            if verify_file(file_path, meta["sha256"]):
                print(f" [SUCCESS] {filename} verified (SHA-256 match).")
            else:
                print(f" [ERROR] SHA-256 mismatch for {filename}!")
                all_ok = False
        except Exception as e:
            print(f" [ERROR] Failed to download {filename}: {e}")
            all_ok = False

    return all_ok

if __name__ == "__main__":
    force_download = "--force" in sys.argv
    success = download_models(force=force_download)
    sys.exit(0 if success else 1)
