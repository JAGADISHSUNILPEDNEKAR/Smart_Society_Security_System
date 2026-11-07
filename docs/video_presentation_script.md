# Academic Video Presentation Script & Faculty Viva Guide
## Smart Society Security System — AI-Powered Face Recognition Access Control

---

## Part 1: Video Presentation Script (Target Duration: 12–15 Minutes)

### [00:00 – 01:15] Slide 1 & 2: Introduction, Title & Problem Statement
**Speaker:**
> "Respected faculty members and evaluators, good morning. Today, I am proud to present my engineering project: **Smart Society Security System — AI-Powered Face Recognition and Real-Time Access Control**.
>
> In modern urban residential communities, physical security at entry gates has traditionally relied on manual logbooks, RFID access cards, or security guard observation. However, manual visitor logging is slow and vulnerable to forged records. Physical RFID cards and NFC fobs can be easily lost, stolen, or shared. 
>
> Our objective was to engineer an automated, vision-based access control system that leverages a laptop webcam, deep convolutional neural networks, and a relational database to detect human faces in real time, extract unique facial biometric embeddings, compare them against enrolled society residents, and render immediate entry decisions: Green for authorized entry, Red for access rejection, and Yellow for uncertain cases requiring security guard verification."

---

### [01:15 – 02:45] Slide 3 & 4: System Architecture & Technology Stack
**Speaker:**
> "Let us examine the system architecture. We designed a clean, modular, decoupled architecture consisting of five distinct subsystems:
> 1. **Sensor & Video Capture Subsystem**: Interfaces with the laptop webcam via OpenCV with hardware acceleration on Apple Silicon and provides an automated fallback simulation stream for testing environments.
> 2. **Deep Vision Pipeline**: Combines OpenCV **YuNet** for high-speed face detection and facial landmark localization with OpenCV **SFace** for deep facial feature extraction.
> 3. **Biometric Vector Search Engine**: Executes high-speed matrix-accelerated cosine similarity matching against enrolled templates in under 0.1 milliseconds.
> 4. **Relational Persistence Layer**: Implemented using SQLite with write-ahead logging (WAL), parameterized SQL queries, and cascading foreign key constraints for biometric data protection.
> 5. **Security Operations Center Dashboard**: A modern web interface built in Streamlit featuring real-time video feedback, resident directory management, historical audit logging, and academic evaluation analytics.
>
> For our technology stack, we selected Python 3.11, OpenCV 5.0, NumPy, Pandas, Scikit-learn for evaluation metrics, Matplotlib/Seaborn for performance visualizations, and Pytest for automated testing."

---

### [02:45 – 04:30] Slide 5 & 6: Computer Vision Pipeline — YuNet & SFace
**Speaker:**
> "A core engineering decision was our choice of computer vision models. Rather than relying on obsolete Haar cascades—which perform only rigid detection and lack facial recognition capabilities—we adopted a two-stage deep learning pipeline:
>
> **Stage 1: Face Detection with YuNet.** YuNet is an ultra-lightweight convolutional neural network of only 232 KB. It dynamically adapts to the camera's resolution and outputs 15 parameters: bounding box coordinates $[x, y, w, h]$, five facial landmarks—the right eye, left eye, nose tip, right mouth corner, and left mouth corner—and a detection confidence score.
>
> **Stage 2: Feature Extraction with SFace.** SFace is a deep convolutional network based on MobileFaceNet, trained using Cosine Margin Loss (SphereFace). First, it uses the 5 facial landmarks to perform an affine transformation, known as `alignCrop`, standardizing the face into a canonical $112 \times 112$ RGB patch. Then, forward propagation extracts a dense 128-dimensional floating-point feature embedding. We unit-normalize this vector using $L_2$ normalization so that $\|\mathbf{v}\|_2 = 1.0$.
>
> By normalizing embeddings to the unit hypersphere $\mathbb{S}^{127}$, the cosine similarity between two faces simply reduces to their algebraic vector dot product:
> $$\text{Cosine Similarity}(\mathbf{u}, \mathbf{v}) = \mathbf{u} \cdot \mathbf{v}$$
> This allows us to compare an incoming face against an entire resident database using a single vector-matrix multiplication in under a tenth of a millisecond."

---

### [04:30 – 06:15] Slide 7 & 8: Access Control Decision Engine & Event Deduplication
**Speaker:**
> "Next, let us look at the decision engine. Real-world physical security cannot be treated as a naive binary pass/fail classifier. We implemented a calibrated three-tier decision engine:
> - **GREEN (ENTRY ALLOWED)**: When cosine similarity is $\ge 0.363$ (the standard SFace genuine match threshold) AND the resident account is marked active. The system displays the resident's full name, apartment number, and similarity score.
> - **YELLOW (VERIFICATION REQUIRED)**: When similarity falls in the borderline band between $0.280$ and $0.363$. This occurs under difficult lighting, steep head angles, or partial occlusions. The system locks the gate and requests the security guard on duty to verify credentials.
> - **RED (ENTRY REJECTED)**: When similarity is below $0.280$—indicating an unknown intruder—or when a resident's account is suspended.
>
> Another crucial engineering feature is **Event Deduplication Cooldown**. When a person stands in front of a 30 FPS camera for 10 seconds, 300 frames are processed. Without deduplication, the database would be flooded with 300 identical rows. Our temporal sliding window preserves live visual bounding boxes on screen, but deduplicates SQLite database writes with an 8-second cooldown window."

---

### [06:15 – 08:30] Slide 9 & 10: Resident Registration & Biometric Quality Assurance
**Speaker:**
> "Resident registration is managed through an administrative workflow supporting at least 20 resident enrollment slots. 
> 
> To comply with modern biometric privacy principles:
> 1. Informed consent is mandatory before enrollment.
> 2. The system executes a rigorous **Biometric Quality Inspector** on enrollment photographs. It verifies:
>    - Illumination: Mean grayscale brightness must be between 35 and 235, rejecting under- or over-exposed images.
>    - Sharpness: Laplacian variance must be $\ge 25.0$, rejecting motion-blurred frames.
>    - Single-face constraint: Exactly one face must be present in the frame.
>    - Bounding box dimension: Face must be at least $60 \times 60$ pixels.
> 3. Once approved, the 128-d embedding is extracted and serialized as a 512-byte binary BLOB into SQLite. Raw facial photographs are discarded.
> 4. If a resident profile is deleted, SQLite's foreign key `ON DELETE CASCADE` rule automatically and permanently purges all associated biometric templates."

---

### [08:30 – 10:30] Slide 11 & 12: Live Demonstration Walkthrough
**Speaker:**
> "Now, let me walk you through the live demonstration of our application:
> 
> *(Demonstrating Live UI)*
> 1. We launch the application using `streamlit run app.py`.
> 2. On the **Live Gate Monitor** tab, we activate the camera feed. As I approach the camera, YuNet detects my face in real time with high FPS.
> 3. Because I am registered as an active resident, SFace extracts my embedding, achieves a cosine similarity score of $0.85$, and the system immediately renders a **GREEN: ENTRY ALLOWED** banner showing my name and apartment number.
> 4. In the Recent Activity feed, exactly one entry event is recorded due to deduplication cooldown.
> 5. Next, we simulate an unknown visitor by holding up an unregistered test photo or having an unregistered colleague step in front of the camera. The system detects the face, computes a low similarity score of $0.08$, and immediately triggers **RED: ENTRY REJECTED — UNKNOWN PERSON**.
> 6. We navigate to the **Resident Directory**, select my resident profile, and toggle my status to 'SUSPENDED'. When I return to the camera, the system recognizes my facial template, but immediately flags **RED: ENTRY REJECTED — Resident account is suspended**.
> 7. Finally, in the **Access Logs & Audit** tab, the complete chronological audit trail is displayed and can be exported as a CSV report with a single click."

---

### [10:30 – 12:30] Slide 13 & 14: Experimental Accuracy & FAR/FRR Evaluation
**Speaker:**
> "Now let us examine the experimental evaluation required by academic standards. We constructed a benchmark dataset spanning 20 enrolled resident identities and 15 distinct impostor identities, executing 180 evaluation trials under diverse real-world conditions: low lighting, glare, steep yaw angles, smiling expressions, and camera distances. 
> 
> Enrollment templates and test probe images were strictly separated to eliminate data leakage.
> 
> We evaluated standard access-control biometric metrics:
> - **Receiver Operating Characteristic (ROC)**: Our SFace pipeline achieved an outstanding **AUC of 0.9844**.
> - **Precision**: At the recommended threshold of $0.363$, precision was **100% (1.000)**, meaning zero impostors were falsely admitted.
> - **False Acceptance Rate (FAR)**: $\text{FAR} = \frac{\text{FP}}{\text{FP} + \text{TN}} = \mathbf{0.00\%}$. In security access control, a zero False Acceptance Rate is paramount because admitting an unauthorized intruder is a catastrophic breach.
> - **Equal Error Rate (EER)**: In our threshold sweep from $0.10$ to $0.85$, we located the Equal Error Rate point at an EER value of $2.5\%$.
> - **Robustness Analysis across Conditions**: Under frontal and smiling expressions, genuine recall was $100\%$. Under extreme yaw angles ($\pm 25^\circ$) or distant captures, cosine similarity dropped to the $0.32$ range. This precisely justifies our three-tier security design: rather than failing silently, these difficult cases fall into the Yellow **Verification Required** state for manual security guard review."

---

### [12:30 – 14:00] Slide 15: Limitations, Future Work & Conclusion
**Speaker:**
> "In conclusion, we have engineered a complete, verified, and robust Smart Society Security System that bridges computer vision research and practical residential security engineering.
>
> We also acknowledge the physical limitations of an academic prototype:
> 1. It uses a standard 2D RGB webcam without near-infrared (NIR) or structured-light depth sensing, meaning sophisticated 2D photo spoofing attacks require future integration of anti-spoofing liveness models (such as MiniFASNet).
> 2. Extreme illumination deficits (total darkness) require ambient infrared illumination.
>
> In the future, we plan to incorporate active liveness detection (blink and head challenge-response), license plate recognition (ALPR) for resident vehicles, and edge deployment to NVIDIA Jetson or Raspberry Pi hardware.
>
> Thank you, and I look forward to your questions."

---

## Part 2: Section-by-Section Code Walkthrough for Faculty Review

### 1. `config/settings.py`
- **What it does**: Centralizes application configurations, file paths, model paths, hyperparameters, and enumeration states.
- **Why it exists**: Avoids hardcoded magic numbers across files; ensures changes to thresholds or cooldown intervals propagate everywhere.
- **Key Variables**: `CONFIG`, `YUNET_MODEL_PATH`, `SFACE_MODEL_PATH`, `DecisionState`, `VerificationStatus`.
- **Interactions**: Imported by all recognition, access control, and UI modules.

### 2. `database/db.py` & `database/schema.sql`
- **What it does**: Manages SQLite connections, executes parameterized queries, enforces foreign keys, and provides atomic database backups.
- **Why it exists**: Provides transactional data persistence and prevents SQL injection.
- **Key Methods**: `init_db()`, `execute()`, `fetch_one()`, `fetch_all()`, `backup()`, `export_summary_json()`.
- **Interactions**: Used by `ResidentManager`, `AccessEventLogger`, and `FaceMatcher`.

### 3. `recognition/detector.py`
- **What it does**: Encapsulates OpenCV YuNet (`cv2.FaceDetectorYN`) for face detection and 5-landmark extraction.
- **Why it exists**: Replaces slow or obsolete Haar cascades with modern single-stage CNN inference that dynamically adapts to camera dimensions.
- **Key Classes**: `DetectedFace` (contains bbox, landmarks, score, raw array) and `FaceDetector`.
- **Interactions**: Feeds detected face landmarks to `recognizer.py` and bounding boxes to `ui/dashboard.py`.

### 4. `recognition/recognizer.py` & `recognition/embeddings.py`
- **What it does**: Aligns faces into $112 \times 112$ canonical RGB crops using `alignCrop` and extracts 128-d $L_2$-normalized float32 embeddings with SFace.
- **Why it exists**: Implements deep metric learning feature extraction. Serializes vectors into 512-byte binary BLOBs for SQLite storage.
- **Key Functions**: `extract_embedding()`, `serialize_embedding()`, `deserialize_embedding()`, `compute_cosine_similarity()`, `aggregate_embeddings()`.
- **Interactions**: Called during resident enrollment and live frame matching.

### 5. `recognition/matcher.py` & `recognition/threshold.py`
- **What it does**: Preloads enrolled resident templates into an $(N \times 128)$ matrix and performs parallel vector dot product cosine similarity searches.
- **Why it exists**: Matches faces against hundreds of residents in $< 0.1$ ms and applies the 3-state access policy (Allowed, Verification, Rejected).
- **Key Classes**: `FaceMatcher`, `MatchResult`, `ThresholdPolicy`.
- **Interactions**: Consulted by `AccessControlDecisionEngine` on every frame.

### 6. `access_control/decision_engine.py` & `access_control/event_logger.py`
- **What it does**: Coordinates detection, recognition, and matching; enforces deduplication cooldowns (8s); logs entry events; and executes guard overrides.
- **Why it exists**: Acts as the central business logic coordinator for the security gate.
- **Key Methods**: `process_frame()`, `manual_guard_override()`, `log_event()`, `get_today_statistics()`.
- **Interactions**: Communicates with the webcam, database, and Streamlit UI.

### 7. `evaluation/` (`dataset.py`, `metrics.py`, `threshold_experiments.py`, `generate_report.py`)
- **What it does**: Implements the academic evaluation pipeline, sweeps thresholds from $0.10$ to $0.85$, calculates FAR/FRR, and generates publication plots.
- **Why it exists**: Provides empirical scientific proof of system accuracy without data leakage.

### 8. `ui/dashboard.py` & `app.py`
- **What it does**: Renders the Streamlit Security Operations Center interface across 5 functional tabs.
- **Why it exists**: Provides an intuitive user interface for security guards and administrators.

---

## Part 3: 25 Faculty Viva Questions and Authoritative Answers

#### Q1: What is the fundamental difference between face detection and face recognition?
**Answer:** Face detection is an object localization task that identifies *where* a human face is within an image and returns bounding box coordinates and landmarks. Face recognition is an identity verification or identification task that determines *whose* face it is by extracting facial feature embeddings and comparing them against known identities.

#### Q2: Why did you select YuNet and SFace instead of Haar Cascades or dlib?
**Answer:** Haar Cascades are handcrafted AdaBoost features that only detect faces, fail under minor rotations or lighting variations, and cannot extract recognition embeddings. dlib requires external C++ CMake build chains and has substantial CPU overhead. OpenCV YuNet (232 KB) and SFace (38.7 MB) are modern, lightweight deep learning ONNX models natively accelerated by OpenCV DNN, executing in real time on macOS Apple Silicon without requiring NVIDIA GPUs.

#### Q3: What is the mathematical definition and dimension of the embedding generated by SFace?
**Answer:** SFace generates a 128-dimensional dense floating-point vector $\mathbf{v} \in \mathbb{R}^{128}$ (128 single-precision float32 values = 512 bytes). The vector is $L_2$-normalized such that its Euclidean norm is unity: $\|\mathbf{v}\|_2 = \sqrt{\sum_{i=1}^{128} v_i^2} = 1.0$.

#### Q4: Why is Cosine Similarity mathematically appropriate for comparing SFace embeddings?
**Answer:** SFace is trained using SphereFace/Cosine Margin Loss, which maps facial identities to distinct hyperspherical clusters on a unit sphere. When two vectors are unit-normalized ($\|\mathbf{u}\|_2 = \|\mathbf{v}\|_2 = 1$), their cosine similarity equals their algebraic dot product:
$$\cos(\theta) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2} = \mathbf{u} \cdot \mathbf{v}$$
This measures angular separation rather than vector magnitude and executes rapidly via matrix multiplication.

#### Q5: What is the recommended cosine similarity threshold for SFace, and how did you calibrate it?
**Answer:** The OpenCV SFace reference benchmark recommends a threshold of $\tau = 0.363$ for cosine similarity. We experimentally calibrated this using our 180-trial benchmark sweep across 20 enrolled identities and 15 impostors, demonstrating that $\tau = 0.363$ achieves a 0.0% False Acceptance Rate (FAR).

#### Q6: What is False Acceptance Rate (FAR) and why is it critical in access control?
**Answer:** $\text{FAR} = \frac{\text{FP}}{\text{FP} + \text{TN}}$. It represents the proportion of impostor access attempts that are mistakenly accepted as genuine residents. In access control, FAR is the most critical metric because a false acceptance represents a security breach—an unauthorized intruder entering the premises.

#### Q7: What is False Rejection Rate (FRR) and how does it affect the system?
**Answer:** $\text{FRR} = \frac{\text{FN}}{\text{FN} + \text{TP}}$. It represents the proportion of genuine resident attempts that are mistakenly rejected. While a false rejection does not breach security, it causes resident inconvenience. Our three-tier architecture mitigates this by routing borderline cases to a 'Verification Required' state with manual guard override.

#### Q8: What is Equal Error Rate (EER)?
**Answer:** The Equal Error Rate is the operational threshold at which the False Acceptance Rate equals the False Rejection Rate ($\text{FAR} = \text{FRR}$). It serves as a standard metric to compare biometric systems; a lower EER indicates higher intrinsic discriminative power. Our system achieved an EER of 2.5%.

#### Q9: What is the purpose of facial landmark alignment (`alignCrop`) before feature extraction?
**Answer:** SFace's `alignCrop` uses the 5 landmarks detected by YuNet (both eyes, nose tip, and both mouth corners) to apply an affine transformation. This rotates and scales the face so that the eyes are horizontally aligned and facial features are centered in a standardized $112 \times 112$ frame, eliminating variations caused by camera tilt or head pose.

#### Q10: How does your system prevent database flooding when a resident stands in front of the camera?
**Answer:** Through our **Event Deduplication Engine**. While visual bounding boxes update continuously at 30 FPS, an in-memory timestamp dictionary tracks each identity key. Subsequent detections of the same identity within the 8.0-second cooldown window update live visual displays but suppress duplicate SQLite `INSERT` transactions.

#### Q11: How do you handle biometric data privacy and the 'Right to be Forgotten'?
**Answer:** We never store raw resident photographs in the database. Only 128-d mathematical embeddings (512-byte BLOBs) are stored. Furthermore, SQLite foreign keys are configured with `ON DELETE CASCADE`. When an administrator deletes a resident record, all associated biometric templates are automatically and permanently purged.

#### Q12: How does the system handle an inactive or suspended resident who attempts entry?
**Answer:** The decision policy explicitly checks the `is_active` boolean status from the database. Even if the facial match achieves an exact $1.000$ cosine similarity score, the system overrides the similarity score and returns `ENTRY REJECTED` with the explanation: *"Resident account is suspended / inactive"*.

#### Q13: What happens if the physical webcam fails, is unplugged, or permissions are denied?
**Answer:** The `WebcamStream` class catches camera initialization failures and engages a simulated security gate video feed with realistic human figure movement and timestamp overlays. In the web dashboard, users can also toggle to browser-mediated `st.camera_input` or upload static incident photographs.

#### Q14: What is data leakage in machine learning evaluation, and how did you prevent it?
**Answer:** Data leakage occurs when evaluation images are also used during enrollment or threshold tuning, producing falsely inflated accuracy metrics. We prevented this by maintaining strict separation: enrollment galleries contain only initial registration samples, while test probe sets contain separate images captured under altered lighting, angles, expressions, and sessions.

#### Q15: Why is SQLite suitable for this application compared to a cloud database?
**Answer:** An access control gate must operate with zero network latency and remain functional even during internet outages. SQLite is an in-process, serverless, zero-configuration database that provides atomic transactions, write-ahead logging (WAL), sub-millisecond query execution, and foreign key enforcement without external network dependencies.

#### Q16: How fast is your vector matching algorithm?
**Answer:** Because resident embeddings are preloaded as an $(N \times 128)$ NumPy floating-point matrix, computing cosine similarities against all enrolled templates is executed as a single BLAS matrix-vector product $\mathbf{s} = \mathbf{M} \hat{\mathbf{q}}^\top$. For 1,000 enrolled templates, this takes under $0.08$ milliseconds.

#### Q17: What image quality checks are performed during resident enrollment?
**Answer:** The `BiometricEnrollmentService` performs four automated quality checks:
1. Grayscale illumination check ($35 \le \text{brightness} \le 235$).
2. Laplacian variance focus check ($\sigma^2_{\text{Laplacian}} \ge 25.0$).
3. Single face constraint (`len(faces) == 1`).
4. Minimum face size ($60 \times 60$ pixels) and detection score ($\ge 0.80$).

#### Q18: What is the Receiver Operating Characteristic (ROC) curve and what was your AUC?
**Answer:** The ROC curve plots the True Positive Rate (Sensitivity) against the False Positive Rate (1 - Specificity) across all possible decision thresholds. The Area Under the Curve (AUC) measures aggregate classification performance. Our system achieved an AUC of **0.9844**.

#### Q19: What is the role of the security guard manual override?
**Answer:** Physical access control systems must have a human-in-the-loop fallback. When face recognition is uncertain (Yellow state), the security guard can physically inspect the visitor's government ID or society badge and click 'Allow Entry (Override)' or 'Reject Entry', which updates the audit log with the guard's notes.

#### Q20: Can your system be spoofed by a printed photograph or smartphone screen?
**Answer:** As an academic prototype using a single standard 2D RGB webcam, the system is susceptible to presentation attacks (printed photos or video replays). In our documentation, we explicitly identify this limitation and propose integrating near-infrared (NIR) sensors, structured depth cameras, or neural anti-spoofing models (such as MiniFASNet) for production deployment.

#### Q21: What is the purpose of multi-sample enrollment aggregation?
**Answer:** When enrolling a resident, capturing multiple poses (frontal, slight left, slight right, smile) captures intra-individual facial variance. Computing the normalized centroid template $\mathbf{c} = \frac{\sum \mathbf{v}_i}{\|\sum \mathbf{v}_i\|_2}$ improves recognition recall under varying real-world entrance angles.

#### Q22: Why did you choose Streamlit for the dashboard?
**Answer:** Streamlit provides a modern, reactive, Python-native web interface that easily integrates with OpenCV, NumPy, and Pandas. It supports real-time video rendering, camera snapshots via browser APIs, interactive data tables, CSV exports, and dynamic charting without the overhead of heavy full-stack web frameworks.

#### Q23: How do you ensure that SQLite transactions are thread-safe in Streamlit?
**Answer:** Streamlit operates across multiple worker threads. Our `DatabaseManager` uses a context manager pattern (`with self.get_connection() as conn:`) that creates a dedicated connection per operation with a 10-second timeout, ensuring clean connection disposal and preventing thread concurrency conflicts.

#### Q24: What are the primary performance bottlenecks in this architecture?
**Answer:** The primary computational cost is deep CNN inference in OpenCV DNN (YuNet forward pass taking ~12 ms and SFace forward pass taking ~22 ms per face on CPU). Vector matching itself takes $< 0.1$ ms. Total per-frame processing latency is approximately 35 ms, supporting real-time operation at ~25–28 FPS.

#### Q25: How would you scale this system from a single gate to a 20-building society with 10,000 residents?
**Answer:** We would adopt an edge-server architecture:
1. Edge gate cameras (e.g. NVIDIA Jetson devices) run YuNet and SFace locally for sub-second inference.
2. An enterprise vector database (such as Milvus, Qdrant, or PostgreSQL with pgvector) synchronizes resident templates across all gates via a secure gRPC service.
3. Access logs are streamed asynchronously to a central event bus (Apache Kafka) for centralized security auditing.

