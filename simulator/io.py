from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np


def load_map(
    path: str | Path,
    resize_hw: Optional[Tuple[int, int]] = None,
) -> np.ndarray:
    """
    Load a top-down map image from disk.

    Returns a uint8 BGR image shaped (H, W, 3).
    - resize_hw: (H, W) if you want to force a standard size.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Map image not found: {path}")

    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Failed to read image: {path}")

    # Handle grayscale → BGR
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    # Handle BGRA → BGR
    if img.ndim == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    if img.ndim != 3 or img.shape[2] != 3:
        raise ValueError(f"Unsupported image format: shape={img.shape}")

    if resize_hw is not None:
        H, W = int(resize_hw[0]), int(resize_hw[1])
        img = cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA)

    return img.astype(np.uint8, copy=False)