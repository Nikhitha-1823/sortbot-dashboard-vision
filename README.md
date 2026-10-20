# SORTBOT-style Delta Robot Dashboard (Starter)

This is a local Flask dashboard starter for a Delta Robot pick-and-place project.

## Current scope
- Responsive dark dashboard inspired by the provided reference screenshots
- Camera placeholder (no camera required yet)
- Clearly labelled demo counts
- Activity and system health panels
- Flask JSON endpoints at `/api/status` and `/api/health`

**Important:** Demo values are not real robot measurements. The dashboard does not move the robot and does not connect to a camera or ESP32 in this starter version.

## 1. Install Python
Use Python 3.10+ if possible. Verify:
```bash
python --version
```
On some systems, use `python3 --version`.

## 2. Create a virtual environment (recommended)
Windows:
```powershell
python -m venv .venv
.venv\Scripts\activate
```
macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install requirements
```bash
python -m pip install -r requirements.txt
```

## 4. Run the dashboard
```bash
python app.py
```
Open `http://127.0.0.1:5000` in your browser. Keep the terminal window open while using the dashboard. Press Ctrl+C to stop.

## Project files
- `app.py`: Flask server and demo API
- `templates/index.html`: dashboard layout
- `static/style.css`: responsive dark theme
- `static/app.js`: clock and API refresh
- `requirements.txt`: Python dependency

## Next integration steps
1. Connect a USB webcam and test it with OpenCV.
2. Add a Python vision module that returns detections (color, bounding box, confidence).
3. Publish real camera frames/detections to the dashboard.
4. Add ESP32 communication over USB serial or Wi-Fi after confirming the firmware protocol.
5. Test servo movements with the robot secured and a clear workspace. Add a physical emergency stop and safe limits before automated motion.

Do not connect or command servos directly from the web page. Route commands through a validated backend/controller, use known-safe motion limits, and verify the power supply and driver wiring first. Do not expose Flask's development server to the public internet.
