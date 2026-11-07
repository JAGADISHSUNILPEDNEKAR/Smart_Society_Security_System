# Codebase Architecture & Code Explanation Guide
## Smart Society Security System — Section-by-Section Engineering Walkthrough

---

## 1. Directory Structure and Module Responsibilities

The codebase follows strict clean-code architecture with high cohesion and loose coupling.

```
Smart_Society_Security_System/
│
├── app.py                         # Streamlit application entry point & page layout router
├── download_models.py             # Model download and SHA-256 verification utility
├── requirements.txt               # Pinned production dependencies
│
├── config/
│   ├── __init__.py                # Package export interface
│   └── settings.py                # Hyperparameters, paths, threshold defaults, enums
│
├── camera/
│   ├── __init__.py                # Camera package interface
│   └── webcam.py                  # OpenCV VideoCapture wrapper, FPS filter, fallback generator
│
├── recognition/
│   ├── __init__.py                # Recognition package interface
│   ├── detector.py                # YuNet FaceDetectorYN wrapper & visual annotator
│   ├── recognizer.py              # SFace FaceRecognizerSF wrapper & 112x112 alignCrop
│   ├── embeddings.py              # NumPy serialization, cosine similarity, vector math
│   ├── threshold.py               # 3-tier threshold decision engine
│   └── matcher.py                 # Fast matrix-accelerated vector template matcher
│
├── database/
│   ├── __init__.py                # Database package interface
│   ├── schema.sql                 # SQLite schema with foreign keys and WAL mode
│   └── db.py                      # Thread-safe DatabaseManager, query executor, backup API
│
├── admin/
│   ├── __init__.py                # Admin package interface
│   ├── resident_manager.py        # Resident directory CRUD & cascading delete
│   ├── enrollment.py              # Biometric quality inspector (brightness, sharpness)
│   └── enrollment_tool.py         # Administrative CLI tool for enrolling volunteers
│
├── access_control/
│   ├── __init__.py                # Access control package interface
│   ├── event_logger.py            # SQLite audit trail logger & statistics aggregator
│   └── decision_engine.py         # Consolidated decision engine & deduplication cooldown
│
├── evaluation/
│   ├── __init__.py                # Evaluation package interface
│   ├── dataset.py                 # Reproducible benchmark generator (gallery vs probes)
│   ├── metrics.py                 # TP, TN, FP, FN, FAR, FRR, ROC calculations
│   ├── threshold_experiments.py   # Threshold parameter sweep & EER identification
│   └── generate_report.py         # Publication-grade chart & table generator
│
├── ui/
│   ├── __init__.py                # UI package interface
│   ├── styles.py                  # SOC dark theme custom CSS styles
│   ├── components.py              # Reusable metric cards, badges, banners
│   └── dashboard.py               # 5 operational tab controllers
│
├── tests/
│   ├── test_database.py           # Relational schema and CRUD unit tests
│   ├── test_recognition.py        # YuNet, SFace, embeddings, and matcher tests
│   ├── test_access_control.py     # Deduplication cooldown and guard override tests
│   ├── test_evaluation.py         # FAR/FRR metrics and benchmark sweep tests
│   └── test_camera.py             # Webcam fallback resilience tests
│
├── models/
│   ├── README.md                  # Model provenance, architecture, and checksums
│   ├── face_detection_yunet_2023mar.onnx
│   └── face_recognition_sface_2021dec.onnx
│
├── reports/
│   ├── figures/                   # Generated evaluation plots (ROC, FAR/FRR, Confusion Matrix)
│   ├── metrics/                   # Generated evaluation CSVs and summary JSON
│   └── final_report.md            # Comprehensive academic final report
│
└── docs/
    ├── architecture.md            # Detailed technical architecture document
    ├── code_explanation.md       # File-by-file code walkthrough (this file)
    ├── testing.md                 # Testing strategy, edge cases, and QA verification
    └── video_presentation_script.md # 10-15 min viva presentation script + 25 Q&As
```

---

## 2. Core Modules Breakdown

### 2.1 Configuration Layer (`config/settings.py`)

#### Purpose
Centralizes all global system settings, hyperparameter defaults, file paths, and enumeration states. Keeping configuration separate from execution logic eliminates hardcoded magic numbers and ensures environment portability.

#### Key Enums and Data Classes
- `DecisionState(Enum)`: Defines the three gate access states:
  - `ALLOWED = "ENTRY ALLOWED"` (Authorized resident, Green)
  - `REJECTED = "ENTRY REJECTED"` (Unknown or suspended identity, Red)
  - `VERIFICATION_REQUIRED = "VERIFICATION REQUIRED"` (Uncertain match, Yellow)
- `VerificationStatus(Enum)`: Tracks human review lifecycle:
  - `AUTOMATIC`: System decided autonomously based on calibrated threshold.
  - `MANUALLY_APPROVED`: Security guard verified physical credentials and overrode status.
  - `MANUALLY_REJECTED`: Security guard intervened to deny entry.
  - `PENDING_REVIEW`: Awaiting human security guard inspection.
- `FaceDetectorConfig`: Encapsulates detection hyperparameters (`score_threshold = 0.80`, `nms_threshold = 0.30`, `min_face_size = 50`).
- `FaceRecognizerConfig`: Encapsulates recognition hyperparameters (`cosine_threshold_high = 0.363`, `cosine_threshold_low = 0.280`, `embedding_dimension = 128`).
- `AccessControlConfig`: Encapsulates temporal constraints (`cooldown_seconds = 8.0`).

---

### 2.2 Database Management Layer (`database/db.py`, `database/schema.sql`)

#### Purpose
Implements persistent storage in SQLite with strict foreign key constraints (`PRAGMA foreign_keys = ON;`), connection management, transaction rollbacks, and administrative backup facilities.

#### Key Functions and Methods
- `DatabaseManager.__init__(db_path)`: Supports both persistent on-disk SQLite files (`smart_society.db`) and in-memory databases (`:memory:`) for isolated, high-speed automated unit testing.
- `get_connection()`: Context manager that yields thread-safe database connections configured with `sqlite3.Row` dictionary factories and foreign key enforcement.
- `init_db(schema_file)`: Reads and executes `database/schema.sql`, creating tables and indexes idempotently (`CREATE TABLE IF NOT EXISTS`).
- `execute(query, params)`: Executes parameterized write queries (`INSERT`, `UPDATE`, `DELETE`) with automatic transaction commit, returning `lastrowid` or `rowcount`.
- `fetch_one(query, params)` / `fetch_all(query, params)`: Executes read queries and returns results as standard Python dictionaries.
- `backup(target_path)`: Uses SQLite's online backup API (`src_conn.backup(dst_conn)`) to produce consistent, non-blocking snapshots without locking active connections.
- `export_summary_json(export_path)`: Generates an administrative JSON audit summary aggregating total resident counts, active residents, biometric templates, and entry statistics.

---

### 2.3 Face Detection Module (`recognition/detector.py`)

#### Purpose
Wraps OpenCV YuNet (`cv2.FaceDetectorYN`) to detect faces, filter noise, clamp bounding box coordinates, and extract 5 key facial landmarks.

#### Key Classes & Functions
- `DetectedFace`: Data container representing a localized face with properties:
  - `bbox`: `(x, y, w, h)` tuple
  - `landmarks`: List of 5 floating-point tuples `[(x1, y1), ..., (x5, y5)]`
  - `score`: Single-stage CNN confidence score $[0.0, 1.0]$
  - `raw_detection`: 15-element NumPy vector required by SFace's `alignCrop` function.
  - `area`: Computed as $w \times h$ to sort candidates by optical prominence.
- `FaceDetector.detect(image)`:
  1. Inspects image resolution $(W, H)$.
  2. Dynamically updates detector input size via `_detector.setInputSize((W, H))` if frame resolution changed.
  3. Executes single-stage CNN inference via `_detector.detect(image)`.
  4. Parses the 15-element detection array, clamps box coordinates to image boundaries, discards detections smaller than `min_face_size` ($50$ px), and sorts faces largest-first.
- `FaceDetector.draw_face_annotations(image, face, color, label, subtext)`: Renders professional cyber-security style bounding boxes with highlighted corner accents, landmark dots, colored classification banners, and similarity subtext.

---

### 2.4 Face Feature Extractor & Recognizer (`recognition/recognizer.py`, `recognition/embeddings.py`)

#### Purpose
Executes facial alignment and deep embedding extraction using OpenCV SFace (`cv2.FaceRecognizerSF`), converting aligned $112 \times 112$ RGB face crops into dense 128-dimensional float32 feature vectors.

#### Key Functions
- `FaceRecognizer.align_and_crop(image, face)`: Invokes `cv2.FaceRecognizerSF.alignCrop` to perform an affine transformation that standardizes eye and nose positions into a $112 \times 112$ RGB face patch.
- `FaceRecognizer.extract_embedding(image, face)`: Executes forward propagation through SFace convolutional layers (`cv2.FaceRecognizerSF.feature`), extracts a raw 128-d vector, and applies $L_2$ unit normalization:
  $$\hat{\mathbf{v}} = \frac{\mathbf{v}}{\|\mathbf{v}\|_2}$$
- `serialize_embedding(vec)`: Converts a 128-dimensional float32 vector into a 512-byte binary string (`vec.tobytes()`) for SQLite BLOB storage.
- `deserialize_embedding(blob)`: Restores a 512-byte BLOB into a normalized NumPy float32 array (`np.frombuffer`).
- `compute_cosine_similarity(v1, v2)`: Computes the dot product of normalized vectors, clamping to $[-1.0, 1.0]$.
- `aggregate_embeddings(list_of_vectors)`: Computes the normalized centroid template from multiple biometric samples enrolled across different angles and expressions.

---

### 2.5 Vector Matcher & Threshold Policy (`recognition/matcher.py`, `recognition/threshold.py`)

#### Purpose
Performs high-speed vector similarity searches against all enrolled resident templates, aggregates scores per resident, and applies the 3-state access policy.

#### Key Classes & Algorithms
- `ThresholdPolicy.classify(similarity, is_active)`:
  - If `not is_active`: Strictly returns `(DecisionState.REJECTED, "Resident account is suspended / inactive")`.
  - If `similarity >= threshold_high` ($0.363$): Returns `(DecisionState.ALLOWED, "High confidence match")`.
  - If `similarity >= threshold_low` ($0.280$): Returns `(DecisionState.VERIFICATION_REQUIRED, "Borderline similarity - Security check required")`.
  - If `similarity < threshold_low`: Returns `(DecisionState.REJECTED, "No confident match - Unknown Individual")`.
- `FaceMatcher.reload_templates()`: Preloads all active resident templates from SQLite into a single contiguous NumPy matrix $\mathbf{M} \in \mathbb{R}^{N \times 128}$.
- `FaceMatcher.match(query_embedding)`:
  - Performs matrix-vector multiplication $\mathbf{s} = \mathbf{M} \hat{\mathbf{q}}^\top$ to compute cosine similarities for all enrolled templates in a single BLAS vector operation ($< 0.1$ ms).
  - Groups scores by resident ID and finds the maximum similarity per resident.
  - Returns `MatchResult` containing resident ID, name, apartment number, similarity score, decision state, and explanation.

---

### 2.6 Access Control Decision Engine & Rate Limiter (`access_control/decision_engine.py`)

#### Purpose
Orchestrates end-to-end frame processing, coordinates detection and matching, applies deduplication rate limiting, and supports manual security guard overrides.

#### Key Methods
- `process_frame(frame)`:
  1. Detects all faces in frame using `FaceDetector`.
  2. For each face, extracts embeddings via `FaceRecognizer` and queries `FaceMatcher`.
  3. Evaluates deduplication cooldown: checks `_last_logged_time[identity_key]`. If within `cooldown_seconds` (8.0s), suppresses duplicate database writes while preserving live visual status banners.
  4. If cooldown expired, logs entry attempt to SQLite via `AccessEventLogger`.
  5. Annotates bounding boxes, landmarks, and top gate decision bar on frame.
- `manual_guard_override(log_id, approve, notes)`: Allows on-duty security guards to manually approve or reject pending access events with recorded audit notes.

---

### 2.7 Biometric Enrollment & Quality Inspector (`admin/enrollment.py`, `admin/resident_manager.py`)

#### Purpose
Enforces quality standards during resident registration to prevent poor-quality, blurry, or multi-face templates from contaminating the gallery.

#### Quality Inspection Steps
1. **Illumination Verification**: Computes mean grayscale intensity. Rejects underexposed ($< 35$) and overexposed ($> 235$) images.
2. **Sharpness Verification**: Calculates Laplacian variance $\sigma^2_{\text{Laplacian}}$. Rejects motion-blurred images ($< 25.0$).
3. **Single Face Verification**: Ensures exactly one face is detected (`len(faces) == 1`). Rejects multiple faces to prevent identity ambiguity.
4. **Dimensions & Confidence**: Verifies face bounding box is at least $60 \times 60$ pixels and detection score $\ge 0.80$.

---

### 2.8 Evaluation & Benchmarking Suite (`evaluation/`)

#### Purpose
Executes rigorous, scientifically valid experimental evaluation of the recognition system across 20 enrolled identities and impostor trials, enforcing strict separation between gallery and probe sets.

#### Modules
- `dataset.py`: Generates reproducible benchmark datasets modeling intra-class variance (lighting, yaw angles, camera distances, expressions) and inter-class orthogonality.
- `metrics.py`: Computes True Positives, True Negatives, False Positives, False Negatives, Accuracy, Precision, Recall, F1, False Acceptance Rate ($\text{FAR} = \frac{\text{FP}}{\text{FP} + \text{TN}}$), and False Rejection Rate ($\text{FRR} = \frac{\text{FN}}{\text{FN} + \text{TP}}$).
- `threshold_experiments.py`: Sweeps thresholds from $0.10$ to $0.85$ (step $0.02$) to identify the Equal Error Rate (EER) and high-security operating points.
- `generate_report.py`: Produces publication-grade visual charts (FAR/FRR curves, ROC curves, Confusion Matrix heatmaps, score distributions) and metric CSV files.

---

### 2.9 Presentation & Dashboard Layer (`app.py`, `ui/`)

#### Purpose
Delivers a responsive Streamlit Security Operations Center (SOC) dashboard.
- Tab 1: **Live Gate Monitor**: Real-time video stream, gate status banner, manual guard override controls, and live activity ticker.
- Tab 2: **Resident Directory**: Filterable member list, active/suspended toggles, and multi-sample biometric enrollment form.
- Tab 3: **Access Logs & Audit**: Searchable historical audit logs with CSV export.
- Tab 4: **Security Settings**: Dynamic threshold sliders, cooldown adjustments, and SQLite database backup buttons.
- Tab 5: **Accuracy & Evaluation**: Live display of ROC curves, FAR/FRR trade-off plots, confusion matrix, and condition breakdown tables.

