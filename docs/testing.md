# Quality Assurance, Edge Case Testing & Verification Guide
## Smart Society Security System

---

## 1. Testing Philosophy and QA Strategy

Access control systems are mission-critical security software. In an access control environment:
- A **False Positive (False Acceptance)** constitutes a security breach (an unauthorized intruder gains access).
- A **False Negative (False Rejection)** causes resident inconvenience (a legitimate resident is temporarily held at the gate).
- A **System Failure or Crash** must fail-closed (access denied, fallback to manual guard control) rather than fail-open.

To guarantee zero regression and robustness, this project implements a multi-tiered test suite spanning unit tests, integration tests, adversarial edge cases, and continuous benchmarking.

---

## 2. Automated Test Suite Summary

The automated test suite is implemented using `pytest` and achieves 100% test passage across 15 comprehensive test modules:

```bash
$ .venv/bin/pytest tests/ -v
============================= test session starts ==============================
platform darwin -- Python 3.11.16, pytest-9.2.0, pluggy-1.7.0
rootdir: /Users/jagadishsunilpednekar/Smart_Society_Security_System

tests/test_access_control.py::test_decision_engine_deduplication PASSED  [  6%]
tests/test_access_control.py::test_guard_override_workflow PASSED        [ 13%]
tests/test_camera.py::test_webcam_stream_simulation_fallback PASSED      [ 20%]
tests/test_camera.py::test_webcam_stream_strict_exception PASSED         [ 26%]
tests/test_database.py::test_schema_initialization PASSED                [ 33%]
tests/test_database.py::test_resident_crud PASSED                        [ 40%]
tests/test_database.py::test_biometric_template_cascading_delete PASSED  [ 46%]
tests/test_database.py::test_access_logger PASSED                        [ 53%]
tests/test_evaluation.py::test_biometric_metrics_calculation PASSED      [ 60%]
tests/test_evaluation.py::test_benchmark_separation_and_sweep PASSED     [ 66%]
tests/test_recognition.py::test_embedding_serialization PASSED           [ 73%]
tests/test_recognition.py::test_cosine_similarity_properties PASSED      [ 80%]
tests/test_recognition.py::test_aggregate_embeddings PASSED              [ 86%]
tests/test_recognition.py::test_threshold_policy PASSED                  [ 93%]
tests/test_recognition.py::test_face_matcher_with_database PASSED        [100%]

============================== 15 passed in 2.51s ==============================
```

---

## 3. Detailed Edge Case Analysis and Test Scenarios

### Edge Case 1: Camera Disconnection / Hardware Failure
- **Condition**: Physical webcam is unplugged, unauthorized by macOS AVFoundation permissions, or executed on a headless CI/CD server.
- **Expected Behavior**: System raises `CameraUnavailableError` in strict mode or seamlessly engages simulated fallback mode without unhandled exceptions.
- **Verification**: Tested in `tests/test_camera.py::test_webcam_stream_simulation_fallback`. Physical camera failure defaults to a synthetic test gate video feed with timestamp overlay.

### Edge Case 2: Inactive or Suspended Resident Identity
- **Condition**: A former tenant moves out or their resident account is suspended (`is_active = 0`), but their biometric template still exists in the database. The individual approaches the gate with an identical face match (similarity $1.000$).
- **Expected Behavior**: The decision engine **MUST REJECT** entry with status `ENTRY REJECTED` and reason `"Resident account is suspended / inactive"`.
- **Verification**: Tested in `tests/test_recognition.py::test_threshold_policy`. Policy guarantees that `is_active == False` preempts any similarity score.

### Edge Case 3: Complete Biometric Template Erasure on Resident Deletion
- **Condition**: A resident requests deletion under privacy compliance (Right to be Forgotten).
- **Expected Behavior**: Deleting the resident row from `residents` must atomically cascade and delete all associated biometric embeddings from `face_embeddings`.
- **Verification**: Tested in `tests/test_database.py::test_biometric_template_cascading_delete`. SQLite's `PRAGMA foreign_keys = ON;` and `ON DELETE CASCADE` guarantee zero orphaned biometric templates.

### Edge Case 4: Event Deduplication / Database Flooding Prevention
- **Condition**: A resident stands in front of the gate camera for 10 seconds. At 30 FPS, 300 video frames are captured.
- **Expected Behavior**: The live video banner must display real-time green bounding boxes on every frame, but the SQLite `access_logs` table must record only **one** entry attempt during the 8-second cooldown window.
- **Verification**: Tested in `tests/test_access_control.py::test_decision_engine_deduplication`. Confirms only 1 database INSERT is committed during the cooldown period.

### Edge Case 5: Uncertain Borderline Match & Security Guard Manual Review
- **Condition**: A resident is partially occluded, resulting in a borderline similarity score between $\tau_{\text{low}}$ ($0.280$) and $\tau_{\text{high}}$ ($0.363$).
- **Expected Behavior**: System transitions to `VERIFICATION REQUIRED` (Yellow banner), leaves gate locked, and alerts the guard. The guard can manually inspect credentials and execute an override.
- **Verification**: Tested in `tests/test_access_control.py::test_guard_override_workflow`. Verifies status transitions from `PENDING_REVIEW` to `MANUALLY_APPROVED` with audit notes.

### Edge Case 6: Duplicate Resident Registration
- **Condition**: An administrator attempts to register two residents with the same Resident ID.
- **Expected Behavior**: Relational primary key constraint prevents duplicate entry and raises a descriptive `ValueError`.
- **Verification**: Tested in `tests/test_database.py::test_resident_crud`.

### Edge Case 7: Quality Inspection on Enrollment
- **Condition**: An administrator attempts to enroll a blurry, underexposed, or multi-face image.
- **Expected Behavior**: The enrollment service inspects mean pixel brightness ($35 \le \mu \le 235$), Laplacian sharpness variance ($\sigma^2 \ge 25.0$), and face count (`len(faces) == 1`). Enrollment is blocked until a compliant photograph is supplied.

---

## 4. Execution Commands for Verification

To execute all tests and verify test coverage:

```bash
# 1. Run all unit and integration tests
.venv/bin/pytest tests/ -v

# 2. Run specific subsystem test suites
.venv/bin/pytest tests/test_recognition.py -v
.venv/bin/pytest tests/test_database.py -v
.venv/bin/pytest tests/test_access_control.py -v

# 3. Execute the full evaluation benchmark suite
.venv/bin/python -m evaluation.generate_report

# 4. Smoke test the Streamlit web dashboard
.venv/bin/streamlit run app.py --server.headless true --server.port 8501
```

