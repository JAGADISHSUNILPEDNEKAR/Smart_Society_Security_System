# Pretrained Deep Learning Models for Smart Society Security

This directory contains the computer vision deep learning models used for face detection and face recognition in the Smart Society Security System.

## Models Overview

### 1. Face Detector: OpenCV YuNet
- **Filename**: `face_detection_yunet_2023mar.onnx`
- **Architecture**: YuNet (Lightweight Convolutional Face Detection Network)
- **Source**: OpenCV Model Zoo (`https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet`)
- **Input Size**: Dynamically configured per frame (default: `320x320` or native camera resolution)
- **Output**: 15 values per detected face:
  - Bounding Box: `[x, y, width, height]`
  - 5 Facial Landmarks: Right Eye `(x, y)`, Left Eye `(x, y)`, Nose Tip `(x, y)`, Right Mouth Corner `(x, y)`, Left Mouth Corner `(x, y)`
  - Detection Confidence Score: `[score]` (0.0 to 1.0)
- **Size**: ~232 KB
- **SHA256**: `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`

### 2. Face Recognizer: OpenCV SFace
- **Filename**: `face_recognition_sface_2021dec.onnx`
- **Architecture**: SFace (SphereFace / MobileFaceNet variant trained with Cosine Margin Loss)
- **Source**: OpenCV Model Zoo (`https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface`)
- **Input**: Aligned & cropped face crop (`112x112x3` RGB)
- **Output**: 128-dimensional dense float32 feature embedding vector
- **Comparison Metric**: Cosine Similarity or Euclidean (L2) distance
- **Reference Threshold**: Cosine Similarity >= 0.363 (L2 Distance <= 1.128)
- **Size**: ~38.7 MB
- **SHA256**: `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`

## Automated Model Download Script

If models are missing or running in a fresh environment, run:
```bash
python download_models.py
```
