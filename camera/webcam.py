"""
Camera Module for Smart Society Security System.
Provides webcam capture with FPS monitoring, error resilience,
and simulated video feed fallback for headless or restricted environments.
"""

import time
import logging
from typing import Optional, Generator
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class CameraError(Exception):
    """Base exception for camera failures."""
    pass

class CameraUnavailableError(CameraError):
    """Raised when the requested camera index cannot be opened or is unauthorized."""
    pass

class WebcamStream:
    """Manages OpenCV VideoCapture with fallback simulation and FPS tracking."""

    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.is_simulated = False
        self._last_frame_time = time.time()
        self._current_fps = 0.0

    def start(self, allow_simulation_fallback: bool = True) -> bool:
        """
        Attempts to open the physical webcam.
        If unavailable and allow_simulation_fallback is True, initializes simulated camera feed.
        """
        logger.info(f"Attempting to open camera device index: {self.camera_index}...")
        self.cap = cv2.VideoCapture(self.camera_index)

        # On macOS, try AVFoundation backend if default index fails
        if not self.cap.isOpened() and hasattr(cv2, "CAP_AVFOUNDATION"):
            logger.info("Retrying with CAP_AVFOUNDATION backend...")
            self.cap.open(self.camera_index, cv2.CAP_AVFOUNDATION)

        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            ret, test_frame = self.cap.read()
            if ret and test_frame is not None:
                self.is_running = True
                self.is_simulated = False
                logger.info(f"Physical camera initialized successfully ({self.width}x{self.height}).")
                return True
            else:
                self.cap.release()
                self.cap = None

        if allow_simulation_fallback:
            logger.warning(
                "Physical camera unavailable or permission denied. "
                "Engaging simulated security feed fallback."
            )
            self.is_running = True
            self.is_simulated = True
            return True
        else:
            raise CameraUnavailableError(
                f"Camera index {self.camera_index} cannot be opened. "
                "Please verify webcam connections and system camera permissions."
            )

    def read_frame(self) -> tuple[bool, Optional[np.ndarray]]:
        """Reads a single frame from physical camera or simulated generator."""
        if not self.is_running:
            return False, None

        current_time = time.time()
        delta = current_time - self._last_frame_time
        if delta > 0:
            self._current_fps = 0.9 * self._current_fps + 0.1 * (1.0 / delta)
        self._last_frame_time = current_time

        if not self.is_simulated and self.cap is not None:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                return True, frame
            logger.warning("Physical camera read failed. Falling back to simulated stream.")
            self.is_simulated = True

        # Generate realistic simulated security gate frame
        sim_frame = self._generate_simulated_frame()
        return True, sim_frame

    def get_fps(self) -> float:
        """Returns smoothed frames per second."""
        return round(self._current_fps, 1)

    def stop(self) -> None:
        """Releases camera resources."""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        logger.info("Camera stream released.")

    def _generate_simulated_frame(self) -> np.ndarray:
        """
        Synthesizes a realistic security checkpoint video frame
        with simulated animated test identity when physical camera is restricted.
        """
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        # Background gradient (gate security hall)
        for y in range(self.height):
            v = int(25 + 35 * (y / self.height))
            frame[y, :] = (v, v, v + 10)

        # Gate entrance overlay text
        cv2.putText(
            frame,
            "GREENFIELD RESIDENTIAL GATE #1 [FEED SIMULATION]",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (200, 200, 200),
            1,
            cv2.LINE_AA
        )

        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            frame,
            f"LIVE: {timestamp_str} | FPS: {self.get_fps()}",
            (20, self.height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 220, 220),
            1,
            cv2.LINE_AA
        )

        # Draw a synthetic test human figure approaching gate
        t = time.time()
        center_x = int(self.width / 2 + 50 * np.sin(t * 0.8))
        center_y = int(self.height / 2 - 10 + 15 * np.cos(t * 0.8))
        radius = 55

        # Head / face oval
        cv2.circle(frame, (center_x, center_y), radius, (205, 185, 175), -1)
        # Eyes
        cv2.circle(frame, (center_x - 18, center_y - 12), 7, (40, 40, 40), -1)
        cv2.circle(frame, (center_x + 18, center_y - 12), 7, (40, 40, 40), -1)
        # Pupils
        cv2.circle(frame, (center_x - 17, center_y - 12), 3, (255, 255, 255), -1)
        cv2.circle(frame, (center_x + 19, center_y - 12), 3, (255, 255, 255), -1)
        # Nose tip
        cv2.circle(frame, (center_x, center_y + 6), 5, (160, 140, 130), -1)
        # Mouth
        cv2.ellipse(frame, (center_x, center_y + 24), (16, 6), 0, 0, 180, (50, 50, 160), 2)
        # Shoulders
        cv2.ellipse(frame, (center_x, center_y + 115), (95, 45), 0, 0, 180, (80, 80, 95), -1)

        return frame

