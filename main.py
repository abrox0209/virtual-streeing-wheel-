"""Virtual Steering - run this file:  python main.py
Options:  python main.py --check   (self-test, no webcam needed)
          python main.py --debug   (extra diagnostic info on screen)
"""
import argparse
import sys
import traceback

from src.config import load_config
from src.steering import SteeringCalculator, hands_angle, hands_distance
from src.utils import FPSCounter, GlobalHotkeys, SteeringError

WINDOW = "Virtual Steering"


def run_check(cfg):
    """Quick self-test of everything that does not need a webcam."""
    from src.hand_tracker import HandTracker
    from src.keyboard_controller import KeyboardController
    import numpy as np
    tracker = HandTracker(cfg["max_hands"], cfg["detection_confidence"],
                          cfg["tracking_confidence"], cfg["steering_landmarks"])
    tracker.process(np.zeros((480, 640, 3), dtype=np.uint8))
    tracker.close()
    print("OK: MediaPipe hand tracker works.")
    kb = KeyboardController(cfg["left_key"], cfg["right_key"])
    kb.release_all()
    print(f"OK: Keyboard input initialised ({kb.mode_name}).")
    print("OK: Self-check passed. Run 'python main.py' to start.")


def run(cfg):
    import cv2
    from src.camera import Camera
    from src.hand_tracker import HandTracker
    from src.keyboard_controller import KeyboardController
    from src.ui import draw_overlay

    debug = cfg["debug"]
    steering = SteeringCalculator(cfg["max_steering_angle"], cfg["deadzone"], cfg["smoothing"])
    keyboard = KeyboardController(
        cfg["left_key"], cfg["right_key"],
        cfg["accelerate_key"] if cfg["enable_acceleration"] else None,
        cfg["brake_key"] if cfg["enable_brake"] else None)
    hotkeys = GlobalHotkeys(cfg["global_hotkeys"])
    fps = FPSCounter()
    camera = tracker = None
    window_shown = False
    keys_enabled = cfg["send_keys_at_start"]
    braking = False
    message, message_frames = "", 0

    try:
        camera = Camera(cfg["camera_index"], cfg["frame_width"], cfg["frame_height"])
        tracker = HandTracker(cfg["max_hands"], cfg["detection_confidence"],
                              cfg["tracking_confidence"], cfg["steering_landmarks"])
        print("Virtual Steering started. C = calibrate, K = keys on/off, Q = quit.")

        while True:
            frame = camera.read()
            if frame is None:
                if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                    break
                continue
            h, w = frame.shape[:2]

            tracking = tracker.process(frame)
            tracker.draw(frame, tracking)

            valid = False
            angle = 0.0
            lp = rp = None
            if tracking.both:
                lp, rp = tracking.left.point, tracking.right.point
                if hands_distance(lp, rp) >= cfg["min_hand_distance"] * w:
                    valid = True
                    angle = hands_angle(lp, rp)
                else:
                    message, message_frames = "Hands too close together", 5

            # ---- keyboard shortcuts (OpenCV window OR global hotkeys) ----
            pressed = hotkeys.poll()
            k = cv2.waitKey(1) & 0xFF
            if k != 255 and chr(k).lower() in "cqkb":
                pressed.add(chr(k).lower())
            if "q" in pressed:
                break
            if "k" in pressed:
                keys_enabled = not keys_enabled
                message, message_frames = ("Keys ON" if keys_enabled else "Keys PAUSED"), 45
            if "b" in pressed and cfg["enable_brake"]:
                braking = not braking
                message, message_frames = ("Brake ON" if braking else "Brake OFF"), 45
            if "c" in pressed:
                if valid:
                    steering.calibrate(angle)
                    message, message_frames = "Calibrated!", 45
                else:
                    message, message_frames = "Calibration failed: show BOTH hands", 60

            # ---- steering ----
            if valid:
                steering.update(angle)
                direction = steering.direction()
            else:
                steering.reset_smoothing()
                direction = 0

            # ---- send keys (release everything when hands are lost) ----
            try:
                if keys_enabled and valid:
                    keyboard.set_steering(direction)
                    keyboard.set_brake(cfg["enable_brake"] and braking)
                    if cfg["enable_acceleration"]:
                        keyboard.set_accelerate(not braking)
                else:
                    keyboard.release_all()
            except OSError as exc:
                raise SteeringError("ERROR: Keyboard input initialization failed.") from exc

            # ---- draw ----
            if tracking.both:
                hands_text = "L+R" + (" (by position)" if tracking.used_fallback else "")
            elif tracking.hands_detected:
                hands_text = "only one hand - show both"
            else:
                hands_text = "none"
            if message_frames > 0:
                message_frames -= 1
            else:
                message = ""
            state = {
                "left_point": lp, "right_point": rp,
                "steering": steering.smoothed if valid else 0.0,
                "angle": steering.relative_angle if valid else 0.0,
                "calibrated": steering.calibrated, "deadzone": steering.deadzone,
                "input_mode": "Keyboard" if keyboard.mode_name == "Keyboard" else keyboard.mode_name,
                "keys_enabled": keys_enabled, "tracking_ok": valid,
                "hands_text": hands_text, "message": message,
                "fps": fps.tick(), "show_fps": cfg["show_fps"], "debug": debug,
                "debug_lines": [
                    f"detected hands: {tracking.hands_detected}",
                    f"raw angle: {angle:+.1f}  center: {steering.center_angle:+.1f}",
                    f"raw steering: {steering.raw:+.1f}  smoothed: {steering.smoothed:+.1f}",
                    f"direction: {direction}  keys held: {keyboard.key_state_text()}",
                ],
            }
            cv2.imshow(WINDOW, draw_overlay(frame, state))
            if not window_shown:
                window_shown = True
            elif cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                break   # user closed the window
    finally:
        keyboard.release_all()      # ALWAYS let go of the keys
        if tracker:
            tracker.close()
        if camera:
            camera.release()
        cv2.destroyAllWindows()
        print("Stopped. All keys released.")


def main():
    parser = argparse.ArgumentParser(description="Virtual Steering")
    parser.add_argument("--check", action="store_true", help="run a self-test and exit")
    parser.add_argument("--debug", action="store_true", help="show debug information")
    args = parser.parse_args()

    cfg, warnings = load_config()
    for w in warnings:
        print("WARNING:", w)
    if args.debug:
        cfg["debug"] = True

    try:
        run_check(cfg) if args.check else run(cfg)
    except SteeringError as exc:
        print(str(exc))
        return 1
    except KeyboardInterrupt:
        print("Interrupted.")
    except Exception as exc:
        if cfg["debug"]:
            traceback.print_exc()
        else:
            print(f"ERROR: Something went wrong ({type(exc).__name__}: {exc}).")
            print("Run 'python main.py --debug' for details.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
