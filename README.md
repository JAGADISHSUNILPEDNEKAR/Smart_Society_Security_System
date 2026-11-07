# Smart Society Security System
### AI-Powered Real-Time Face Recognition & Biometric Access Control

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![OpenCV 5.0](https://img.shields.io/badge/OpenCV-5.0.0-green.svg)](https://opencv.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.42+-red.svg)](https://streamlit.io/)
[![Tests Passing](https://img.shields.io/badge/pytest-15%2F15%20passed-brightgreen.svg)]()
[![ROC AUC](https://img.shields.io/badge/ROC%20AUC-0.9844-success.svg)]()

---

## 1. Project Overview

The **Smart Society Security System** is an enterprise-grade, edge-deployable computer vision security platform engineered for residential communities. The application utilizes a standard laptop webcam to monitor residential society entrance gates in real time, executing deep convolutional neural network pipelines for single-stage face detection, landmark alignment, and deep feature embedding extraction.

Detected faces are matched against a database of pre-registered residents in an SQLite relational database. Access decisions are rendered instantly with high-visibility color-coded feedback:
- **GREEN**: **ENTRY ALLOWED** (Recognized active resident, gate unlocked).
- **YELLOW**: **VERIFICATION REQUIRED** (Borderline score, security guard manual review mandated).
- **RED**: **ENTRY REJECTED** (Unknown individual or suspended resident account, gate remains locked).

An integrated **Event Deduplication Sliding Window** prevents database log flooding, and a **Security Operations Center (SOC) Dashboard** in Streamlit provides complete administrative control, resident directory management, and real-time audit logging.

---

## 2. Key Features

- **Real-Time Webcam Vision Pipeline**: Dynamically captures and processes live video frames with hardware acceleration on Apple Silicon and Intel hardware.
- **Deep Learning Models (OpenCV Zoo)**:
  - **OpenCV YuNet**: Single-stage CNN face detector (~232 KB) outputting bounding boxes and 5 facial landmarks.
  - **OpenCV SFace**: SphereFace / MobileFaceNet deep feature extractor (~38.7 MB) outputting 128-dimensional dense float32 normalized embeddings.
- **Three-Tier Access Decision Engine**:
  - Genuine Match: Cosine Similarity $\ge 0.363 \implies$ **ENTRY ALLOWED (Green)**
  - Borderline Match: $0.280 \le \text{Similarity} < 0.363 \implies$ **VERIFICATION REQUIRED (Yellow)**
  - Intruder / No Match: $\text{Similarity} < 0.280 \implies$ **ENTRY REJECTED (Red)**
- **Event Deduplication Engine**: Enforces a configurable 8-second temporal cooldown to prevent database flooding when a resident stands in front of the camera.
- **Security Guard Manual Override**: Allows on-duty guards to inspect physical credentials and approve or deny uncertain access events with recorded audit notes.
- **Biometric Privacy Safeguards**: Stores only irreversible 128-d floating-point vectors (512 bytes per template) in SQLite BLOBs; raw photographs are never permanently retained.
- **Cascading Biometric Deletion**: Relational foreign keys (`ON DELETE CASCADE`) guarantee that deleting a resident profile permanently purges all associated biometric templates.
- **Automated Biometric Quality Inspector**: Verifies illumination, focus sharpness, single-face constraints, and bounding box dimensions during enrollment.
- **Scientific Evaluation Suite**: Computes FAR, FRR, ROC curves ($\text{AUC} = 0.9844$), and Confusion Matrices across 180 evaluation trials.

---

## 3. Technology Stack

- **Language**: Python 3.11.16
- **Computer Vision**: OpenCV 5.0.0 (OpenCV DNN with YuNet & SFace ONNX)
- **Mathematical Core**: NumPy, SciPy, Scikit-learn
- **Database**: SQLite with Write-Ahead Logging (WAL) and Foreign Key enforcement
- **Dashboard UI**: Streamlit 1.42+
- **Visualizations**: Matplotlib, Seaborn
- **Testing**: Pytest (15 automated unit and integration tests)

---

## 4. Installation and Setup

### Prerequisites
- macOS (Apple Silicon or Intel), Linux, or Windows
- Python 3.10 or 3.11 installed
- Laptop webcam or USB camera

### Quick Setup

```bash
# 1. Clone or navigate to the repository
cd /Users/jagadishsunilpednekar/Smart_Society_Security_System

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Verify / Download deep learning models (automatically verifies SHA-256)
python download_models.py

# 4. Verify automated test suite passes (15/15 passed)
pytest tests/ -v
```

---

## 5. Execution Guide

### Launching the Streamlit SOC Dashboard
To start the interactive web application:

```bash
source .venv/bin/activate
streamlit run app.py
```
Then open your web browser at **`http://localhost:8501`**.

---

## 6. How to Register Residents

The system supports registering at least 20 resident slots through two workflows:

### Method A: Via the Web Dashboard (Recommended)
1. Open the dashboard at `http://localhost:8501`.
2. Navigate to the **`👥 Resident Directory`** tab on the left sidebar.
3. Expand **`➕ Register & Enroll New Resident`**.
4. Enter:
   - **Resident ID**: e.g., `RES-101`
   - **Full Name**: e.g., `Aarav Patel`
   - **Apartment**: e.g., `Tower-A 402`
   - **Phone**: e.g., `+91-9876543210`
   - **Informed Consent**: Check the mandatory consent affirmation.
5. Capture a photo using **Browser Webcam Snapshot** or upload a portrait file.
6. The real-time **Biometric Quality Inspector** will verify brightness, sharpness, and single-face criteria.
7. Click **`💾 Confirm & Save Resident Enrollment`**.

### Method B: Via Administrative CLI Tool
```bash
python admin/enrollment_tool.py \
  --id "RES-102" \
  --name "Priya Sharma" \
  --apartment "Tower-B 104" \
  --image "/path/to/portrait.jpg" \
  --consent
```

---

## 7. How to Demonstrate Live System Workflows

### 1. Demonstrating Authorized Entry (GREEN)
1. In the sidebar, select **`📹 Live Gate Monitor`**.
2. Select **`Laptop Webcam (Continuous)`** and check **`🟢 Activate Continuous Video Stream`** (or use **`Browser Camera Snapshot`**).
3. Position an enrolled resident in front of the camera.
4. The system detects the face, extracts the 128-d embedding, achieves a cosine similarity score $> 0.363$, and renders:
   - **Green Bounding Box** around the face.
   - **Top Decision Bar**: `● ENTRY ALLOWED: AARAV PATEL (Apartment Tower-A 402)`.
   - The event is logged once to the Recent Gate Activity feed.

### 2. Demonstrating Unauthorized Intrusion Rejection (RED)
1. Have an unregistered individual or hold up an unregistered portrait in front of the camera.
2. SFace extracts the embedding, but the top similarity score is low ($< 0.280$).
3. The system renders:
   - **Red Bounding Box** around the face.
   - **Top Decision Bar**: `● ENTRY REJECTED: UNKNOWN PERSON`.
   - The unauthorized intrusion is recorded in the audit logs.

### 3. Demonstrating Suspended Resident Rejection (RED)
1. Navigate to **`👥 Resident Directory`**.
2. Select an enrolled resident and click **`Suspend / Deactivate`**.
3. Return to the live camera and position that resident in front of the lens.
4. The system recognizes the resident's biometric template, but the decision engine intercepts the inactive status and flags:
   - **Red Status**: `● ENTRY REJECTED: AARAV PATEL (SUSPENDED)`.

### 4. Demonstrating Security Guard Manual Override (YELLOW)
1. When a borderline score ($0.280 \le S < 0.363$) occurs, the gate displays:
   - **Yellow Status**: `● VERIFICATION REQUIRED`.
2. Under **`Manual Security Guard Override`**, the on-duty guard inspects physical credentials, enters notes, and clicks **`✔ Allow Entry (Override)`** or **`✖ Reject Entry`**.
3. The audit log updates with status `MANUALLY_APPROVED`.

---

## 8. Experimental Evaluation Results

To execute the benchmark and regenerate all evaluation charts:

```bash
python -m evaluation.generate_report
```

All figures are saved to `reports/figures/` and metrics to `reports/metrics/`.

### Benchmark Results (180 Trials Across 20 Enrolled Identities)

| Metric | Measured Value | Standard Target | Status |
| :--- | :--- | :--- | :--- |
| **Total Test Trials** | 180 | $\ge 100$ | PASS |
| **Genuine Resident Trials** | 120 | $\ge 50$ | PASS |
| **Impostor Intrusion Trials** | 60 | $\ge 30$ | PASS |
| **Receiver Operating Characteristic (ROC AUC)** | **0.9844** | $> 0.95$ | EXCELLENT |
| **Operating Precision** | **1.0000 (100%)** | $> 0.95$ | OPTIMAL |
| **False Acceptance Rate (FAR)** | **0.0000 (0.00%)** | $< 0.01$ | ZERO BREACHES |
| **Equal Error Rate (EER)** | **0.0250 (2.50%)** | $< 0.05$ | HIGH ACCURACY |
| **Per-Frame Latency** | **34.8 ms (~28 FPS)** | $< 50$ ms | REAL-TIME |

---

## 9. Academic Project Documentation Directory

- **Technical Architecture Guide**: [`docs/architecture.md`](docs/architecture.md)
- **File-by-File Code Walkthrough**: [`docs/code_explanation.md`](docs/code_explanation.md)
- **Quality Assurance & Testing Guide**: [`docs/testing.md`](docs/testing.md)
- **Faculty Video Presentation Script & 25 Viva Q&As**: [`docs/video_presentation_script.md`](docs/video_presentation_script.md)
- **Comprehensive Academic Final Report**: [`reports/final_report.md`](reports/final_report.md)
- **Model Checksums and Architecture**: [`models/README.md`](models/README.md)

