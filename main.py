import cv2
import easyocr
import re
import sqlite3
import numpy as np
from datetime import datetime
from ultralytics import YOLO
from collections import defaultdict
import time
import os

# -------------------------------
# SNAPSHOT FOLDER
# -------------------------------
SNAPSHOT_DIR = "snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# -------------------------------
# BLACKLIST 🚨
# -------------------------------
BLACKLIST = {
    "AGG 7148",
    "ABC 1234",
    "ADE 3450"
}

# -------------------------------
# LOAD MODEL
# -------------------------------
model = YOLO("runs/detect/train/weights/best.pt")
reader = easyocr.Reader(['en'], gpu=False)

# -------------------------------
# DATABASE
# -------------------------------
conn = sqlite3.connect("plates.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS plates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate TEXT,
    confidence INTEGER,
    time TEXT,
    image_path TEXT,
    status TEXT
)
""")
conn.commit()

# -------------------------------
# VIDEO
# -------------------------------
cap = cv2.VideoCapture("zim5.mp4")

if not cap.isOpened():
    print("❌ Cannot open video")
    exit()

# -------------------------------
# MEMORY
# -------------------------------
plate_votes = defaultdict(int)
last_seen_time = {}
frame_count = 0

# SETTINGS
MIN_CONF = 60
VOTE_THRESHOLD = 4
COOLDOWN = 10

# -------------------------------
# CLEAN TEXT
# -------------------------------
def clean_text(text):
    text = re.sub(r'[^A-Z0-9]', '', text.upper())
    if len(text) > 7:
        text = text[-7:]
    return text

# -------------------------------
# LOOP
# -------------------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    if frame_count % 40 == 0:
        plate_votes.clear()

    results = model(frame)

    for r in results:
        boxes = r.boxes.xyxy.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy()

        for box, conf in zip(boxes, confs):

            conf_percent = int(conf * 100)

            if conf_percent < MIN_CONF:
                continue

            x1, y1, x2, y2 = map(int, box)

            # -------------------------------
            # CROP
            # -------------------------------
            pad = 25
            x1 = max(0, x1 - pad)
            y1 = max(0, y1 - pad)
            x2 = min(frame.shape[1], x2 + pad)
            y2 = min(frame.shape[0], y2 + pad)

            plate_img = frame[y1:y2, x1:x2]

            if plate_img.size == 0:
                continue

            # -------------------------------
            # PREPROCESS
            # -------------------------------
            gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, None, fx=3, fy=3)
            gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=25)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)

            thresh = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY_INV,
                15, 5
            )

            kernel = np.ones((3,3), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

            # -------------------------------
            # OCR
            # -------------------------------
            text = "".join(reader.readtext(
                thresh,
                detail=0,
                allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            ))

            text = clean_text(text)

            print("OCR:", text)

            # -------------------------------
            # VALIDATE
            # -------------------------------
            match = re.search(r'[A-Z]{3}[0-9]{4}', text)

            if not match:
                continue

            plate_text = match.group()
            plate_text = plate_text[:3] + " " + plate_text[3:]

            print("✅ VALID:", plate_text)

            # -------------------------------
            # VOTING
            # -------------------------------
            plate_votes[plate_text] += 1

            best_plate = max(plate_votes, key=plate_votes.get)
            best_count = plate_votes[best_plate]

            current_time = time.time()

            # -------------------------------
            # FINAL DECISION
            # -------------------------------
            if best_count >= VOTE_THRESHOLD:

                if best_plate in last_seen_time:
                    if current_time - last_seen_time[best_plate] < COOLDOWN:
                        continue

                last_seen_time[best_plate] = current_time

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # -------------------------------
                # 🚨 BLACKLIST CHECK
                # -------------------------------
                if best_plate in BLACKLIST:
                    status = "BLACKLISTED"
                    color = (0, 0, 255)  # RED
                    print("🚨 ALERT! BLACKLISTED:", best_plate)
                else:
                    status = "NORMAL"
                    color = (0, 255, 0)  # GREEN

                # -------------------------------
                # SAVE SNAPSHOT
                # -------------------------------
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{best_plate.replace(' ', '_')}_{timestamp}.jpg"
                image_path = os.path.join(SNAPSHOT_DIR, filename)

                cv2.imwrite(image_path, plate_img)

                # -------------------------------
                # SAVE TO DATABASE
                # -------------------------------
                cursor.execute("""
                    INSERT INTO plates (plate, confidence, time, image_path, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (best_plate, conf_percent, now, image_path, status))

                conn.commit()

                print("💾 SAVED:", best_plate, status)

                plate_votes.clear()

            # -------------------------------
            # DRAW
            # -------------------------------
            label = f"{plate_text} ({conf_percent}%)"

            if plate_text in BLACKLIST:
                color = (0,0,255)
            else:
                color = (0,255,0)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            cv2.putText(frame, label, (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    cv2.imshow("ANPR SYSTEM", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
conn.close()