
import cv2
import numpy as np

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)

if not camera.isOpened():
    print("Camera unavailable.")
    raise SystemExit

# HSV color ranges: suitable starting values.
ranges = {
    "RED": [
        ((0, 100, 70), (10, 255, 255)),
        ((170, 100, 70), (179, 255, 255))
    ],
    "GREEN": [((35, 70, 50), (85, 255, 255))],
    "BLUE": [((90, 70, 50), (135, 255, 255))],
    "YELLOW": [((20, 100, 100), (35, 255, 255))]
}

print("Color detection running. Press Q to quit.")

while True:
    ok, frame = camera.read()
    if not ok:
        print("Unable to read camera.")
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    for color, bands in ranges.items():
        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)

        for lower, upper in bands:
            mask |= cv2.inRange(
                hsv,
                np.array(lower, dtype=np.uint8),
                np.array(upper, dtype=np.uint8)
            )

        mask = cv2.medianBlur(mask, 5)
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        for contour in contours:
            if cv2.contourArea(contour) < 1200:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(
                frame, (x, y), (x + w, y + h),
                (255, 255, 255), 2
            )
            cv2.putText(
                frame, color, (x, max(y - 8, 20)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (255, 255, 255), 2
            )

    cv2.imshow("SORTBOT - Color Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
