from flask import Flask, request, jsonify, render_template, send_from_directory
import cv2
import numpy as np
import easyocr
import re
import os
import sqlite3
from datetime import datetime
from ultralytics import YOLO

app = Flask(__name__)

# -------------------------------
# SETUP
# -------------------------------
model = YOLO("runs/detect/train/weights/best.pt")
reader = easyocr.Reader(['en'], gpu=False)

# 🚨 BLACKLIST
BLACKLIST = [
    "AEJ 7544",
    "ADT 9282",
    "ADX 3291",
    "AHG 9615"   # test plate
]

# Ensure snapshots folder exists
os.makedirs("snapshots", exist_ok=True)

# -------------------------------
# CREATE DATABASE
# -------------------------------
conn = sqlite3.connect("plates.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS plates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate TEXT,
    confidence REAL,
    timestamp TEXT,
    image_path TEXT,
    status TEXT
)
""")

conn.commit()
conn.close()

# -------------------------------
# CLEAN TEXT
# -------------------------------
def clean_text(text):
    text = re.sub(r'[^A-Z0-9]', '', text.upper())
    if len(text) > 7:
        text = text[-7:]
    return text

# -------------------------------
# HOME — redirect to dashboard
# -------------------------------
@app.route("/")
def home():
    conn = sqlite3.connect("plates.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT plate, confidence, timestamp, image_path, status
        FROM plates
        ORDER BY id DESC
        LIMIT 50
    """)
    plates = cursor.fetchall()
    conn.close()
    return render_template("index.html", plates=plates)

# -------------------------------
# SERVE SNAPSHOTS
# -------------------------------
@app.route('/snapshots/<path:filename>')
def snapshots(filename):
    return send_from_directory('snapshots', filename)

# -------------------------------
# DETECT
# -------------------------------
@app.route('/detect', methods=['POST'])
def detect():
    try:
        file = request.files['image'].read()
        npimg = np.frombuffer(file, np.uint8)
        frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        results = model(frame)

        for r in results:
            boxes = r.boxes.xyxy.cpu().numpy()
            confs = r.boxes.conf.cpu().numpy()

            for box, conf in zip(boxes, confs):
                x1, y1, x2, y2 = map(int, box)

                plate_img = frame[y1:y2, x1:x2]

                if plate_img.size == 0:
                    continue

                gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
                gray = cv2.resize(gray, None, fx=3, fy=3)

                text = "".join(reader.readtext(
                    gray,
                    detail=0,
                    allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                ))

                text = clean_text(text)

                match = re.search(r'[A-Z]{3}[0-9]{4}', text)

                if match:
                    plate = match.group()
                    plate = plate[:3] + " " + plate[3:]

                    print("✅ DETECTED:", plate)

                    # 🚨 CHECK BLACKLIST
                    status = "NORMAL"
                    if plate in BLACKLIST:
                        status = "BLACKLISTED"
                        print("🚨 ALERT! BLACKLISTED:", plate)

                    # -------------------------------
                    # SAVE IMAGE
                    # -------------------------------
                    filename = f"snapshots/{plate}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    cv2.imwrite(filename, plate_img)

                    # -------------------------------
                    # SAVE TO DB
                    # -------------------------------
                    conn = sqlite3.connect("plates.db")
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT INTO plates (plate, confidence, timestamp, image_path, status)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        plate,
                        float(conf),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        filename,
                        status
                    ))

                    conn.commit()
                    conn.close()

                    return jsonify({
                        "plate": plate,
                        "status": status
                    })

        return jsonify({
            "plate": "No plate detected",
            "status": "NONE"
        })

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return jsonify({
            "plate": "Error processing image",
            "status": "ERROR"
        })

# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)