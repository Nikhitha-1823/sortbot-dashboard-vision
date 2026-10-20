from flask import Flask,Response, jsonify, render_template,send_from_directory,request
import cv2
from datetime import datetime
import time

app = Flask(__name__)
started_at = time.time()
camera_connected = False

# Phase 1 intentionally uses DEMO data. No camera or robot is connected yet.
# Replace these values with real data as camera/ESP32 integration is added.
DEMO_MODE = False
live_counts = {
    "RED": 0,
    "GREEN": 0,
    "BLUE": 0,
    "YELLOW": 0
}
tally_counts = {
    "RED" : 0,
    "GREEN" : 0,
    "BLUE" : 0,
    "YELLOW" : 0,
}
demo_counts = {"RED": 0, "GREEN": 0, "BLUE": 0, "YELLOW": 0}
demo_activity = [
    {"color": "GREEN", "message": "Demo event: object classified", "detail": "No robot action performed", "duration": "—", "ok": None},
    {"color": "RED", "message": "Demo event: sorting target selected", "detail": "Waiting for camera and ESP32", "duration": "—", "ok": None},
    {"color": "BLUE", "message": "Demo event: dashboard initialized", "detail": "Sample data only", "duration": "—", "ok": None},
]
live_activity = []
@app.route("/")
def index():
    return render_template("index.html", demo_mode=DEMO_MODE)

@app.route("/api/status")
def status():
    return jsonify({
        "demo_mode": DEMO_MODE,
        "camera": "Connected" if camera_connected else "Not connected",
        "vision": "Running" if camera_connected else "Not started",
        "esp32": "Not connected",
        "communication": "Not configured",
        "robot_state": "Demo/idle",
        "process_stage": app.config.get("process_stage",0),
        "counts" : live_counts,
        "total" : sum(live_counts.values()),
        "success_rate": None,
        "avg_cycle_seconds": None,
        "uptime_seconds": int(time.time() - started_at),
        "last_update": datetime.now().isoformat(timespec="seconds"),
        "activity": live_activity if not DEMO_MODE else demo_activity
    })

@app.before_request
def reset_counts_on_dashboard_refresh():
    global tally_counts
    if request.path == "/":
        tally_counts = {"RED": 0, "GREEN": 0, "BLUE": 0, "YELLOW": 0}

@app.route("/api/health")


def health():
    return jsonify({
        "dashboard": "Running",
        "camera": "Connected" if camera_connected else "Not connected",
        "python_vision": "Running" if camera_connected else "Not started",
        "esp32": "Not connected",
        "mode": "DEMO" if DEMO_MODE else "LIVE"
    })




@app.route("/api/reset", methods=["POST"])
def reset_counts():
    global tally_counts, live_activity

    tally_counts = {
        "RED": 0,
        "GREEN": 0,
        "BLUE": 0,
        "YELLOW": 0
    }
    live_activity = []

    return jsonify({
        "success": True,
        "message": "Counts reset successfully"
    })
def generate_camera_frames():
    global camera_connected, live_counts,tally_counts

    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not camera.isOpened():
        print("ERROR: Webcam could not be opened")
    else:
        print("SUCCESS: Webcam opened")
    camera_connected = camera.isOpened()

    color_ranges = {
        "RED": [
            ((0, 100, 80), (10, 255, 255)),
            ((170, 100, 80), (180, 255, 255))
        ],
        "GREEN": [((35, 70, 60), (85, 255, 255))],
        "BLUE": [((90, 70, 60), (130, 255, 255))],
        "YELLOW": [((20, 100, 100), (35, 255, 255))]
    }
    previous_colors = set()
    previous_counted_colors = set()
    color_missing_frames = {
    "RED": 0,
    "GREEN": 0,
    "BLUE": 0,
    "YELLOW": 0
    }

    color_seen_frames = {
        "RED": 0,
        "GREEN": 0,
        "BLUE": 0,
        "YELLOW": 0
    }
    
    
    try:
        while camera.isOpened():
            success, frame = camera.read()
            camera_connected = success

            if not success:
                live_counts = {
                    "RED": 0, "GREEN": 0,
                    "BLUE": 0, "YELLOW": 0
                }
                break

            # Count objects currently visible in this frame.
            frame_counts = {
                "RED": 0, "GREEN": 0,
                "BLUE": 0, "YELLOW": 0
            }

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            for color, ranges in color_ranges.items():
                mask = None

                for lower, upper in ranges:
                    part = cv2.inRange(
                        hsv, tuple(lower), tuple(upper)
                    )
                    mask = (
                        part if mask is None
                        else cv2.bitwise_or(mask, part)
                    )

                # Reduce small specks and camera noise.
                mask = cv2.morphologyEx(
                    mask, cv2.MORPH_OPEN,
                    cv2.getStructuringElement(
                        cv2.MORPH_ELLIPSE, (5, 5)
                    )
                )

                contours, _ = cv2.findContours(
                    mask, cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE
                )

                
                for contour in contours:
                    if cv2.contourArea(contour) < 3000:
                        continue

                    x, y, w, h = cv2.boundingRect(contour)
                    frame_counts[color] += 1

                    cv2.rectangle(
                        frame, (x, y), (x + w, y + h),
                        (255, 255, 255), 2
                    )
                    cv2.putText(
                        frame, color, (x, max(y - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (255, 255, 255), 2
                    )
            
            current_colors = {
                color for color, count in frame_counts.items()
                if count > 0
            }
            process_stage = 1 if current_colors else 0
            app.config["process_stage"] = process_stage
            for color in current_colors - previous_colors:
                live_activity.insert(0, {
                    "color": color,
                    "message": f"{datetime.now().strftime('%H:%M:%S')} — {color} object detected",
                    "detail": "Detected by live camera",
                    "duration": "—",
                    "ok": None
                })

            live_activity[:] = live_activity[:20]
            previous_colors = current_colors.copy()
    

            # Publish this frame's counts to the dashboard API.
            # Publish current frame detections to the dashboard.
            live_counts = frame_counts.copy()

# Count a color when it first appears in view.
            # Confirm a color is visible for several frames before counting.
            # Count a color when it first appears in view.
# Confirm a color is visible for several frames before counting.
            for color in color_seen_frames:
                if frame_counts[color] > 0:
                    color_seen_frames[color] += 1
                    color_missing_frames[color] = 0
                else:
                    color_seen_frames[color] = 0
                    color_missing_frames[color] += 1
                    if color_missing_frames[color] >= 20:
                        previous_counted_colors.discard(color)
                    

                if (
                    color_seen_frames[color] >= 5
                    and color not in previous_counted_colors
                ):
                    tally_counts[color] += 1
                    previous_counted_colors.add(color)

# Remember which colors are currently visible.
            
            success, buffer = cv2.imencode(".jpg", frame)
            if not success:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + buffer.tobytes()
                + b"\r\n"
            )

    finally:
        camera.release()
        camera_connected = False
        live_counts = {
            "RED": 0, "GREEN": 0,
            "BLUE": 0, "YELLOW": 0
        }



@app.route("/camera_feed")
def camera_feed():
    return Response(
        generate_camera_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/mobile")
def mobile():
    return send_from_directory("mobile_design", "SORTBOT.html")


if __name__ == "__main__":
    # Local-only development server. Do not expose this port to the public internet.
    app.run(host="0.0.0.0", port=5000, debug=True)
   