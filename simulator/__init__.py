"""
MicroUAV_2D simulator package.

Ultra-light 2D planar "down-cam" drone sandbox:
- Load a top-down map image.
- Move a point-drone with WASD / arrows.
- Extract a fixed-size FOV crop (pad-with-zeros or clamp).
- Render map + drone + FOV overlay + HUD.

No NDVI/VARI. This is a generic overhead-image navigation sandbox.
"""

from .core import DroneState, MicroUAV2D
from .io import load_map
from .render import draw_drone_overlay, make_side_by_side_view

__all__ = [
    "DroneState",
    "MicroUAV2D",
    "load_map",
    "draw_drone_overlay",
    "make_side_by_side_view",
]