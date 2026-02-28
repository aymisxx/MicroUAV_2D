from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from .core import MicroUAV2D
from .io import load_map
from .render import draw_drone_overlay, make_side_by_side_view


def _key_to_action(key: int) -> int | None:
    """
    Map WASD keys to the 4 actions:
    0=up, 1=right, 2=down, 3=left
    """
    if key in (ord("w"), ord("W")):
        return 0
    if key in (ord("d"), ord("D")):
        return 1
    if key in (ord("s"), ord("S")):
        return 2
    if key in (ord("a"), ord("A")):
        return 3

    return None


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="microuav_2d",
        description="MicroUAV_2D - 2D down-cam drone navigation sandbox"
    )
    p.add_argument("--map", type=str, required=True, help="Path to overhead map image (png/jpg).")
    p.add_argument("--fov", type=int, default=128, help="FOV size for square crop (default: 128).")
    p.add_argument("--fov_w", type=int, default=None, help="Optional rectangular FOV width.")
    p.add_argument("--fov_h", type=int, default=None, help="Optional rectangular FOV height.")
    p.add_argument("--step", type=int, default=8, help="Step size in pixels (default: 8).")
    p.add_argument("--border", choices=["pad", "clamp"], default="pad", help="Border handling for crop.")
    p.add_argument("--resize_h", type=int, default=None, help="Optional resize height.")
    p.add_argument("--resize_w", type=int, default=None, help="Optional resize width.")
    return p


def main() -> None:
    args = build_argparser().parse_args()

    # Resize sanity: either provide both, or none
    if (args.resize_h is None) ^ (args.resize_w is None):
        raise ValueError("Provide both --resize_h and --resize_w, or provide neither.")

    resize_hw = None
    if args.resize_h is not None and args.resize_w is not None:
        resize_hw = (int(args.resize_h), int(args.resize_w))

    world = load_map(Path(args.map), resize_hw=resize_hw)

    fov_w = int(args.fov_w) if args.fov_w is not None else int(args.fov)
    fov_h = int(args.fov_h) if args.fov_h is not None else int(args.fov)

    sim = MicroUAV2D(
        world_bgr=world,
        fov_w=fov_w,
        fov_h=fov_h,
        step_size=int(args.step),
        border_mode=args.border,
    )

    cv2.namedWindow("MicroUAV_2D", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("MicroUAV_2D", 1400, 800)

    paused = False

    while True:
        obs = sim.get_observation()

        hud = (
            f"x={sim.state.x}  y={sim.state.y}",
            f"step={sim.step_size}  fov={sim.fov_w}x{sim.fov_h}  border={sim.border_mode}",
            "WASD: move   R: reset   SPACE: pause   Q: quit",
        )

        left = draw_drone_overlay(sim.world, sim.state, sim.fov_w, sim.fov_h, hud_lines=hud)

        scale = 4
        fov_big = cv2.resize(
            obs,
            (obs.shape[1] * scale, obs.shape[0] * scale),
            interpolation=cv2.INTER_NEAREST,
        )

        frame = make_side_by_side_view(left, fov_big, right_title="FOV (crop)")

        cv2.imshow("MicroUAV_2D", frame)

        key = cv2.waitKey(16)

        if key == -1:
            continue

        # Quit
        if key in (ord("q"), ord("Q"), 27):
            break

        # Reset
        if key in (ord("r"), ord("R")):
            sim.reset()
            continue

        # Pause toggle
        if key == ord(" "):
            paused = not paused
            continue

        if paused:
            continue

        action = _key_to_action(key)
        if action is not None:
            sim.step(action)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()