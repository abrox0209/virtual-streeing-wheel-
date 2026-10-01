# Virtual Steering (version 1)

Steer browser games (e.g. on poki.com) by holding both hands in front of your webcam
like a steering wheel. Your hand angle becomes a steering value from **-100% (left) to +100% (right)**,
which is turned into **LEFT / RIGHT keyboard key presses**.

```
Webcam -> MediaPipe Hands -> steering angle -> smoothing -> keyboard keys -> browser game
```

## What you need
* Windows 10/11, 64-bit
* **Python 3.12 (64-bit)** from <https://www.python.org/downloads/> (tick *Add python.exe to PATH*)
* A webcam, and VS Code (optional)

## Installation (PowerShell, in the project folder)
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
If PowerShell says scripts are disabled, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

**Shortcut:** double-click `setup.bat` once, then `run.bat` any time.

Check your installation without a webcam: `python main.py --check`
Run the tests: `python -m unittest discover -s tests -v`

## Using it with a browser game (e.g. Poki)
1. Open the Poki game and **find its controls** (usually on the start/help screen). Make sure it uses keyboard steering.
2. Start the program (`run.bat`). A window with your camera appears.
3. **Click the game** so the browser has keyboard focus.
4. Hold both hands up like on a wheel, level and straight.
5. Press **C** to calibrate. The screen shows `CALIBRATED`.
6. Tilt your hands left/right as if turning a wheel.
7. Press **Q** to stop. All keys are released.

Keys **C, Q, K, B** are detected globally (Windows), so they work while the game window is in front.
Note that the game also receives those letter presses; if a game uses one of them,
set `"global_hotkeys": false` in `config.json` and then click the camera window before pressing C/Q/K.

Other keys: **K** = pause/resume sending keys, **B** = toggle brake (only if `enable_brake` is on).

> **Mr Racer's exact controls were NOT verified.** Check the game's own control instructions and set the keys below.
> Some browser games block or ignore simulated keyboard input; this program uses Windows hardware-scancode
> input (the most compatible method), but no method is guaranteed. Games running as Administrator
> cannot receive keys from a normal program.

## Changing the keys (`config.json`)
Open `config.json` in VS Code, edit, save, restart the program.

Arrow keys (default):
```json
"left_key": "left",
"right_key": "right"
```
A / D keys:
```json
"left_key": "a",
"right_key": "d"
```
Allowed key names: letters `a`-`z`, digits `0`-`9`, `left right up down space enter shift ctrl tab esc`.

## Settings
| Setting | Meaning |
|---|---|
| `camera_index` | 0 = first camera. Try 1 if you have several cameras |
| `smoothing` | Weight of the new reading: `1.0` = no smoothing, `0.2` = smooth (default), `0.05` = very smooth/slow |
| `deadzone` | Percent around the center where no key is pressed (default 10) |
| `max_steering_angle` | Hand tilt in degrees that equals 100% (default 45). Smaller = more sensitive |
| `min_hand_distance` | Minimum distance between hands (fraction of the image width) |
| `steering_landmarks` | Hand points used for steering: 0 = wrist, 5 = index knuckle, 9 = middle knuckle (averaged). Full list: MediaPipe hand landmarks 0-20 |
| `enable_acceleration` / `accelerate_key` | Hold the accelerate key while both hands are visible (default off) |
| `enable_brake` / `brake_key` | Press **B** to toggle brake (default off). Brake replaces acceleration while on |
| `send_keys_at_start` | `false` = start with keys paused (press K to enable) |
| `global_hotkeys` | C/Q/K/B work while another window has focus |
| `debug` | Extra diagnostics on screen (or run `python main.py --debug`) |

Invalid values never crash the program: it prints a warning and uses a safe default.

## Safety
LEFT/RIGHT (and accelerate/brake) are released when: hands disappear, you press Q, you close the window,
the webcam disconnects, or the program crashes (`try/finally` plus an exit hook).
LEFT and RIGHT are never held at the same time.

## How it works
* `src/hand_tracker.py` - MediaPipe Hands (`mp.solutions.hands`, bundled model, nothing downloaded at run time). The image is mirrored first, so MediaPipe's Left/Right labels are your real hands. If it labels both hands the same, hands are told apart by screen position (shown as "by position").
* `src/steering.py` - angle of the line between your two hands -> -100..+100%, smoothing, calibration.
* `src/keyboard_controller.py` - single input method: Windows `SendInput` with scan codes (no extra libraries, so no conflicting key presses).
* `src/ui.py` - simple overlay. `src/config.py` - safe `config.json` loading.

## Dependencies
Pinned in `requirements.txt` (Python 3.12): `mediapipe==0.10.14`, `opencv-contrib-python==4.10.0.84`, `numpy==1.26.4`.
MediaPipe requires `opencv-contrib-python`, so **do not install `opencv-python`** next to it (they conflict).
Newer MediaPipe versions may remove the `mp.solutions` API, which is why the version is pinned.

## Troubleshooting
* *Could not open webcam*: close Zoom/Teams/etc., check Windows camera privacy settings, try `"camera_index": 1`.
* *Steering is reversed*: calibrate again with hands level; make sure the right hand is on the right of the screen.
* *Jittery*: lower `smoothing` (e.g. 0.1) or raise `deadzone`.
* *Too twitchy / needs big turns*: raise / lower `max_steering_angle`.
* *Game ignores keys*: click the game first, check its keys, and try the other key set (arrows vs A/D).
