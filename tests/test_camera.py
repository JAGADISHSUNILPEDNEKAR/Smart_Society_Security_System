"""
Unit tests for WebcamStream and camera error resilience.
"""

import pytest
import numpy as np
from camera.webcam import WebcamStream, CameraUnavailableError

def test_webcam_stream_simulation_fallback():
    """Ensures camera engages realistic simulation fallback when physical index is inaccessible."""
    # Using non-existent device index 99 to test fallback
    cam = WebcamStream(camera_index=99, width=320, height=240)
    success = cam.start(allow_simulation_fallback=True)

    assert success is True
    assert cam.is_running is True
    assert cam.is_simulated is True

    ret, frame = cam.read_frame()
    assert ret is True
    assert frame is not None
    assert frame.shape == (240, 320, 3)
    assert cam.get_fps() >= 0.0

    cam.stop()
    assert cam.is_running is False

def test_webcam_stream_strict_exception():
    """Ensures CameraUnavailableError is raised if simulation fallback is disallowed."""
    cam = WebcamStream(camera_index=99)
    with pytest.raises(CameraUnavailableError):
        cam.start(allow_simulation_fallback=False)

