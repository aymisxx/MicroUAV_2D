from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple

import numpy as np


BorderMode = Literal["pad", "clamp"]


@dataclass
class DroneState:
    """Point-drone state in pixel coordinates."""
    x: int
    y: int


class MicroUAV2D:
    """
    Minimal 2D planar drone simulator over a static overhead image.

    Design:
    - 4-direction discrete actions: up/right/down/left
    - movement clamped to stay inside map bounds
    - fixed-size centered observation window, zero-padded at borders (default)
    """

    # 0=up, 1=right, 2=down, 3=left
    ACTIONS = {0: "up", 1: "right", 2: "down", 3: "left"}

    def __init__(
        self,
        world_bgr: np.ndarray,
        fov_w: int = 128,
        fov_h: int = 128,
        step_size: int = 8,
        border_mode: BorderMode = "pad",
        start_xy: Tuple[int, int] | None = None,
    ) -> None:
        if world_bgr.ndim != 3 or world_bgr.shape[2] not in (3, 4):
            raise ValueError("world_bgr must be an image array shaped (H, W, 3) or (H, W, 4).")

        if fov_w <= 0 or fov_h <= 0:
            raise ValueError("fov_w and fov_h must be positive.")
        if step_size <= 0:
            raise ValueError("step_size must be positive.")
        if border_mode not in ("pad", "clamp"):
            raise ValueError("border_mode must be 'pad' or 'clamp'.")

        # Keep BGR for OpenCV display. If 4-ch, we drop alpha in observations.
        self.world = world_bgr
        self.H, self.W = int(world_bgr.shape[0]), int(world_bgr.shape[1])

        self.fov_w = int(fov_w)
        self.fov_h = int(fov_h)
        self.step_size = int(step_size)
        self.border_mode: BorderMode = border_mode

        if start_xy is None:
            start_x, start_y = self.W // 2, self.H // 2
        else:
            start_x, start_y = int(start_xy[0]), int(start_xy[1])

        self.state = DroneState(
            x=int(np.clip(start_x, 0, self.W - 1)),
            y=int(np.clip(start_y, 0, self.H - 1)),
        )

    def reset(self, start_xy: Tuple[int, int] | None = None) -> DroneState:
        if start_xy is None:
            self.state.x = self.W // 2
            self.state.y = self.H // 2
        else:
            self.state.x = int(np.clip(int(start_xy[0]), 0, self.W - 1))
            self.state.y = int(np.clip(int(start_xy[1]), 0, self.H - 1))
        return self.state

    def step(self, action: int) -> DroneState:
        """
        Apply a discrete action:
        0=up, 1=right, 2=down, 3=left

        Position is clamped to remain within image bounds.
        """
        a = int(action)
        if a not in self.ACTIONS:
            raise ValueError(f"Invalid action {action}. Expected one of {list(self.ACTIONS.keys())}.")

        dx, dy = 0, 0
        if a == 0:      # up
            dy = -self.step_size
        elif a == 1:    # right
            dx = self.step_size
        elif a == 2:    # down
            dy = self.step_size
        elif a == 3:    # left
            dx = -self.step_size

        self.state.x = int(np.clip(self.state.x + dx, 0, self.W - 1))
        self.state.y = int(np.clip(self.state.y + dy, 0, self.H - 1))
        return self.state

    def get_observation(self) -> np.ndarray:
        """
        Return the down-cam crop centered at (x, y).

        Default behavior:
        - fixed-size patch
        - zero-padded when near borders (pad mode)

        Returns: uint8 array of shape (fov_h, fov_w, 3) in BGR.
        """
        x, y = self.state.x, self.state.y
        return self._crop_centered(self.world, x, y, self.fov_w, self.fov_h, self.border_mode)

    @staticmethod
    def _crop_centered(
        img: np.ndarray,
        cx: int,
        cy: int,
        w: int,
        h: int,
        border_mode: BorderMode,
    ) -> np.ndarray:
        # Compute desired bounds
        x0 = cx - (w // 2)
        y0 = cy - (h // 2)
        x1 = x0 + w
        y1 = y0 + h

        H, W = img.shape[0], img.shape[1]
        C = img.shape[2]

        if border_mode == "clamp":
            # Clamp bounds; crop may shrink near edges
            x0c, y0c = max(0, x0), max(0, y0)
            x1c, y1c = min(W, x1), min(H, y1)
            crop = img[y0c:y1c, x0c:x1c]
        else:
            # Pad-with-zeros (stable output shape)
            pad_x0 = max(0, -x0)
            pad_y0 = max(0, -y0)
            pad_x1 = max(0, x1 - W)
            pad_y1 = max(0, y1 - H)

            x0c, y0c = max(0, x0), max(0, y0)
            x1c, y1c = min(W, x1), min(H, y1)

            crop = img[y0c:y1c, x0c:x1c]

            if pad_x0 or pad_y0 or pad_x1 or pad_y1:
                out = np.zeros((h, w, C), dtype=img.dtype)
                yy0 = pad_y0
                yy1 = yy0 + crop.shape[0]
                xx0 = pad_x0
                xx1 = xx0 + crop.shape[1]
                out[yy0:yy1, xx0:xx1] = crop
                crop = out

        # Drop alpha if present
        if crop.ndim == 3 and crop.shape[2] == 4:
            crop = crop[:, :, :3]

        return crop.astype(np.uint8, copy=False)