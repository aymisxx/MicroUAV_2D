from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np

from .core import DroneState


def draw_drone_overlay(
    world_bgr: np.ndarray,
    state: DroneState,
    fov_w: int,
    fov_h: int,
    hud_lines: Tuple[str, ...] = (),
) -> np.ndarray:
    """
    Return a copy of the world image with:
    - drone marker (filled circle)
    - FOV rectangle centered at drone
    - optional HUD text
    """
    img = world_bgr.copy()

    cx, cy = int(state.x), int(state.y)

    # Drone marker
    cv2.circle(img, (cx, cy), radius=6, color=(255, 255, 255), thickness=-1)  # white fill
    cv2.circle(img, (cx, cy), radius=6, color=(0, 0, 0), thickness=2)        # black edge

    # FOV rectangle (same bounds as crop logic)
    x0 = cx - (fov_w // 2)
    y0 = cy - (fov_h // 2)
    x1 = x0 + fov_w
    y1 = y0 + fov_h
    cv2.rectangle(img, (x0, y0), (x1, y1), color=(0, 0, 255), thickness=2)   # red box

    # HUD
    y = 24
    for line in hud_lines:
        cv2.putText(
            img,
            line,
            (12, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            img,
            line,
            (12, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )
        y += 26

    return img


def make_side_by_side_view(
    left_bgr: np.ndarray,
    right_bgr: np.ndarray,
    right_title: str = "FOV",
) -> np.ndarray:
    """
    Make a single combined frame:
    [left global view | right FOV view]

    The right panel is resized to match left height.
    """
    left = left_bgr
    right = right_bgr

    # Resize right to match left height
    H = left.shape[0]
    rh, rw = right.shape[0], right.shape[1]
    scale = H / float(rh)
    new_w = max(1, int(rw * scale))
    right_rs = cv2.resize(right, (new_w, H), interpolation=cv2.INTER_NEAREST)

    # Add title on right
    cv2.putText(
        right_rs,
        right_title,
        (12, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        right_rs,
        right_title,
        (12, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
    )

    return np.concatenate([left, right_rs], axis=1)