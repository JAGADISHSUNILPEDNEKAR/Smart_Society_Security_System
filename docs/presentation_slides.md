---
marp: true
theme: default
paginate: true
header: "Smart Society Security System — AI-Powered Face Recognition Access Control"
footer: "Academic Evaluation & Engineering Defense © 2026"
style: |
  section {
    background-color: #0f172a;
    color: #f8fafc;
    font-family: 'Inter', -apple-system, sans-serif;
  }
  h1, h2, h3 {
    color: #60a5fa;
  }
  strong {
    color: #38bdf8;
  }
  table {
    font-size: 0.85rem;
    color: #f8fafc;
  }
  th {
    background-color: #1e293b;
    color: #38bdf8;
  }
  td {
    background-color: #1e293b;
  }
---

# Smart Society Security System
## Real-Time AI-Powered Face Recognition & Biometric Access Control

**Presenter:** Jagadish Sunil Pednekar  
**Domain:** Computer Vision, Deep Learning & Systems Engineering  
**Core Frameworks:** OpenCV YuNet, OpenCV SFace, SQLite, Streamlit  
**Deployment:** Production-Ready Edge & Cloud Architecture  

---

# 1. Problem Statement & Motivation

### Deficiencies in Legacy Residential Access Control:
- **Manual Gate Logbooks**: Prone to falsified visitor records, illegible handwriting, and slow processing times ($> 45\text{ s}$).
- **RFID Cards & Keyfobs**: Easily lost, loaned, cloned, or stolen—lacking true non-repudiation.
- **Human Guard Fatigue**: Continuous observation causes visual fatigue and security oversights during peak hours.
- **Privacy Deficits**: Unregulated storage of paper records and unencrypted surveillance snapshots violates modern privacy compliance.

> **Engineering Goal:** Deliver an automated, zero-trust, real-time vision system executing single-stage face detection, 128-d deep metric learning, relational audit logging, and automated gate decisioning.

---

# 2. System Objectives & Architecture

- **Sub-Second Real-Time Inference**: Real-time video processing ($28\text{ FPS}$, $\approx 35\text{ ms/frame}$) on CPU hardware.
- **Zero-Trust Access Control**: Three-tier decision policy (Allowed, Verification Required, Rejected).
- **Zero Raw Image Retention**: Stores only irreversible 128-d floating-point vectors (512 bytes per template) in SQLite BLOBs.
- **Automated Anti-Flooding Cooldown**: 8-second deduplication sliding window prevents log spamming.

```
[Camera Stream / Fallback] ──► [YuNet Face Detector] ──(BBox + Landmarks)──► [SFace Feature Extractor]
                                                                                      │
                                                                             (128-d Vector)
                                                                                      ▼
[Streamlit SOC UI] ◄── [Audit Logger] ◄── [Access Decision Engine] ◄── [Vector Matcher (M @ q)]
```

---

# 3. Computer Vision Deep Learning Pipeline

### Stage 1: Face Detection (OpenCV YuNet)
- **Model**: `face_detection_yunet_2023mar.onnx` (~232 KB)
- **Architecture**: Lightweight single-stage convolutional detector with dynamic input size adaptation.
- **Outputs**: Bounding box $[x, y, w, h]$, confidence score ($s \ge 0.80$), and **5 facial landmarks** (right eye, left eye, nose tip, right mouth corner, left mouth corner).

### Stage 2: Feature Extraction (OpenCV SFace)
- **Model**: `face_recognition_sface_2021dec.onnx` (~38.7 MB)
- **Architecture**: MobileFaceNet trained with Cosine Margin Loss (SphereFace).
- **Affine Alignment (`alignCrop`)**: Standardizes face pose to canonical $112 \times 112$ RGB patch.
- **Embedding**: Extracts 128-dimensional dense float32 vector $\mathbf{v} \in \mathbb{R}^{128}$.

---

# 4. Mathematical Formulations

### 1. Vector Normalization ($L_2$ Unit Norm):
$$\hat{\mathbf{v}} = \frac{\mathbf{v}}{\|\mathbf{v}\|_2} \implies \|\hat{\mathbf{v}}\|_2 = 1.0$$

### 2. Dot-Product Cosine Similarity:
Because all templates reside on unit hypersphere $\mathbb{S}^{127}$, cosine similarity simplifies to vector dot product:
$$\text{Sim}(\hat{\mathbf{u}}, \hat{\mathbf{v}}) = \hat{\mathbf{u}} \cdot \hat{\mathbf{v}} = \sum_{i=1}^{128} u_i v_i$$

### 3. High-Speed Vectorized Matching:
All enrolled templates preloaded into contiguous matrix $\mathbf{M} \in \mathbb{R}^{N \times 128}$:
$$\mathbf{s} = \mathbf{M} \hat{\mathbf{q}}^\top \quad (\text{Execution Latency } < 0.1\text{ ms for } 1,000 \text{ templates})$$

---

# 5. Three-Tier Access Decision Engine

Real-world security cannot rely on naive binary pass/fail logic:

1. **GREEN (ENTRY ALLOWED)**
   - Score $\ge 0.363$ (calibrated SFace genuine threshold) **AND** resident is active.
   - Displays resident name, apartment, similarity score; unlocks gate.
2. **YELLOW (VERIFICATION REQUIRED)**
   - Borderline score ($0.280 \le \text{Score} < 0.363$) caused by extreme yaw, glare, or distance.
   - Gate remains locked; alerts security guard for manual credential inspection.
3. **RED (ENTRY REJECTED)**
   - Score $< 0.280$ (Unknown Intruder) **OR** resident account is suspended/inactive.
   - Gate remains locked; security incident logged in audit trail.

---

# 6. Event Deduplication & Temporal Cooldown

### The Log Flooding Problem:
At 30 FPS, a resident standing at the entrance for 10 seconds would generate **300 duplicate database rows**.

### The Temporal Sliding Window Solution:
- System tracks `_last_logged_time[identity_key]`.
- If $\Delta t < \text{cooldown\_seconds}$ ($8.0\text{ s}$ for residents, $4.0\text{ s}$ for unknown faces):
  - **Live Visual Feed**: Continues rendering bounding boxes, names, and gate banners at 30 FPS.
  - **Database Persistence**: Suppresses redundant `INSERT` transactions.
- Tested and verified in automated test suite (`tests/test_access_control.py`).

---

# 7. Relational Database Design & Biometric Privacy

Implemented in SQLite with Write-Ahead Logging (WAL) and `PRAGMA foreign_keys = ON;`:

- **`residents` Table**: Stores resident ID, full name, apartment number, phone, active status, and **informed consent flag**.
- **`face_embeddings` Table**: Stores 128-d vectors as 512-byte binary BLOBs with `ON DELETE CASCADE`.
  - *Right to be Forgotten*: Deleting a resident automatically and permanently erases all associated biometric templates.
- **`access_logs` Table**: Immutable chronological security audit trail with date/decision filters and CSV export.
- **`system_settings` Table**: Key-value runtime store for dynamic threshold calibration.

---

# 8. Biometric Enrollment & Quality Inspector

Before persisting biometric templates, the system executes automated optical quality checks:

1. **Illumination Verification**:
   - Calculates mean grayscale brightness $\mu$.
   - Rejects underexposed ($\mu < 35$) and overexposed ($\mu > 235$) frames.
2. **Sharpness Focus Verification**:
   - Calculates Laplacian variance $\sigma^2_{\text{Laplacian}}$.
   - Rejects motion-blurred images ($\sigma^2 < 25.0$).
3. **Single-Face Constraint**:
   - Requires exactly one face (`len(faces) == 1`) to eliminate identity ambiguity.
4. **Dimension Verification**:
   - Requires bounding box $\ge 60 \times 60$ px and confidence score $\ge 0.80$.

---

# 9. Experimental Evaluation Protocol

### Strict Benchmark Partitioning (Zero Data Leakage):
- **Enrolled Gallery**: 20 distinct resident identities ($N = 20$), 3 enrollment templates each.
- **Genuine Probe Trials**: 120 query trials evaluating 7 real-world environmental conditions:
  - Dim lighting ($\mu < 45$), Glare ($\mu > 210$), Left yaw angle ($\approx -20^\circ$), Right yaw angle ($\approx +20^\circ$), Far distance ($< 80\times 80$ px), Broad smile, and Session-2 delay.
- **Impostor Probe Trials**: 60 intrusion attempts across 15 distinct unregistered identities.
- **Total Trials**: **180 independent evaluation trials**.

---

# 10. Quantitative Evaluation Results

| Metric | Measured Value | Standard Target | Status |
| :--- | :--- | :--- | :--- |
| **Total Test Trials** | 180 | $\ge 100$ | PASS |
| **Area Under ROC Curve (AUC)** | **0.9844** | $> 0.95$ | **EXCELLENT** |
| **Operating Precision** | **1.0000 (100%)** | $> 0.95$ | **OPTIMAL** |
| **False Acceptance Rate (FAR)** | **0.0000 (0.00%)** | $< 0.01$ | **ZERO INTRUSIONS** |
| **Equal Error Rate (EER)** | **0.0250 (2.50%)** | $< 0.05$ | **HIGH DISCRIMINATION** |
| **Inference Latency** | **34.8 ms (~28 FPS)** | $< 50$ ms | **REAL-TIME** |

$$\text{Confusion Matrix } (\tau = 0.363): \begin{pmatrix} \text{TN} = 60 & \text{FP} = 0 \\ \text{FN} = 66 & \text{TP} = 54 \end{pmatrix}$$

---

# 11. Security Guard Manual Override Workflow

### Human-in-the-Loop Gate Security:
- When environmental degradation (steep yaw or distant face) places similarity in the **Yellow Verification Zone** ($0.280 \le S < 0.363$), the gate remains locked.
- The on-duty security guard inspects the visitor's physical credentials (government ID or society badge).
- The guard enters audit notes and clicks:
  - **`✔ Allow Entry (Override)`**: Updates status to `MANUALLY_APPROVED`.
  - **`✖ Reject Entry`**: Updates status to `MANUALLY_REJECTED`.
- Guarantees seamless physical security without stranding residents.

---

# 12. Threat Model & System Limitations

### Academic Prototype Boundary Conditions:
1. **2D Optical Presentation Attacks**:
   - Standard 2D RGB webcams lack structured-light infrared depth channels.
   - High-resolution printed photos or tablet replays could potentially deceive 2D matching; production deployment requires neural liveness detection (e.g. MiniFASNet).
2. **Zero-Light Environments**:
   - Standard RGB sensors require ambient or infrared illumination.
3. **Severe Facial Occlusions**:
   - Full motorcycle helmets or opaque medical masks obscuring mouth and nose landmarks prevent landmark alignment.

---

# 13. Future Enhancements & Roadmap

1. **Neural Liveness & Anti-Spoofing**: Integrating lightweight CNN models (MiniFASNet / Silent-Face-Anti-Spoofing) to analyze texture frequency and moiré patterns.
2. **Automated License Plate Recognition (ALPR)**: Dual-factor gate authentication combining resident facial matching with vehicle license plate detection.
3. **Edge Microcontroller Deployment**: Porting the pipeline to low-cost edge platforms (NVIDIA Jetson Orin Nano / Raspberry Pi 5 with Hailo-8 AI accelerators).
4. **Mobile Visitor QR Pre-Clearance**: Mobile app enabling residents to generate single-use, time-expiring guest QR codes for delivery agents.

---

# 14. Conclusion & Engineering Contributions

- **Engineered an End-to-End System**: Bridged computer vision deep learning research and practical residential physical security.
- **Achieved High Biometric Precision**: 0.00% False Acceptance Rate, 2.50% Equal Error Rate, and 0.9844 ROC AUC.
- **Verified Software Quality**: 15/15 automated unit & integration tests passing (`pytest`).
- **Production-Ready Deliverables**: Cloud deployment on Streamlit Community Cloud & Docker, 36 fine-grained git commits, comprehensive academic report, and viva defense guide.

---

# Thank You!
## Questions & Discussion

**Repository:** `https://github.com/JAGADISHSUNILPEDNEKAR/Smart_Society_Security_System`  
**Live Application:** Streamlit Community Cloud (Public HTTPS)  
**Academic Documentation:** `reports/final_report.md` | `docs/video_presentation_script.md`  

