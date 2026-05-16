# ANPR Backend — Automatic Number Plate Recognition

A Flask-based REST API and web dashboard for detecting and logging vehicle number plates using YOLOv8 and EasyOCR.

---

## Project Structure

```
anpr_project/
├── api.py                  # Main Flask app — detection API + dashboard
├── main.py                 # Standalone video processing script (local use)
├── app.py                  # Legacy dashboard (replaced by api.py)
├── database.py             # Legacy DB helper
├── requirements.txt        # Python dependencies
├── start.sh                # Render startup script (downloads model + starts server)
├── render.yaml             # Render deployment config
├── data.yaml               # YOLO dataset config
├── templates/
│   └── index.html          # Dashboard UI
├── snapshots/              # Saved plate images (auto-created)
├── plates.db               # SQLite database (auto-created)
└── runs/
    └── detect/
        └── train/
            └── weights/
                └── best.pt # Trained YOLO model weights
```

---

## Features

- **YOLOv8** plate detection on uploaded images
- **EasyOCR** for reading plate text
- **Blacklist** checking with instant alert status
- **SQLite** database logging all detections
- **Web dashboard** showing recent detections with images
- **REST API** for integration with mobile apps (Flutter, etc.)
- **Snapshot saving** — crops and saves each detected plate image

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web dashboard |
| POST | `/detect` | Detect plate from uploaded image |
| GET | `/health` | Check if model is loaded |
| GET | `/snapshots/<filename>` | Serve plate snapshot images |

### POST `/detect`

**Request:** `multipart/form-data` with field `image` (JPEG/PNG)

**Response:**
```json
{"plate": "AGI 4580", "status": "NORMAL"}
{"plate": "AEJ 7544", "status": "BLACKLISTED"}
{"plate": "No plate detected", "status": "NONE"}
{"plate": "Model not loaded", "status": "ERROR"}
```

---

## Running Locally

### 1. Clone the repo
```bash
git clone https://github.com/musazulu/number-plate--detection.git
cd number-plate--detection
```

### 2. Create a virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add the YOLO model
Place your trained model at:
```
runs/detect/train/weights/best.pt
```

### 5. Run the API server
```bash
python api.py
```
Server starts at `http://localhost:5000`

### 6. Run the video processor (optional)
Edit `main.py` to point to your video file, then:
```bash
python main.py
```

---

## Testing the API

### Using curl
```bash
curl -X POST http://localhost:5000/detect \
  -F "image=@path/to/plate_image.jpg"
```

### Using Postman
1. Method: `POST`
2. URL: `http://localhost:5000/detect`
3. Body → form-data → key: `image`, type: File
4. Select your image and send

---

## Deployment on Render

The app is deployed at:
**https://number-plate-detection-8e4q.onrender.com**

### How it works on Render
1. `start.sh` runs on deploy
2. Downloads `best.pt` from Google Drive (if not cached)
3. Starts `gunicorn api:app` with 120s timeout

### Environment
- Runtime: Python 3.11
- Build Command: `pip install -r requirements.txt`
- Start Command: `bash start.sh`

> **Note:** The free Render tier has 512MB RAM. Loading EasyOCR + YOLO requires ~1GB. Upgrade to the Starter plan ($7/month) for reliable performance.

---

## Database Schema

```sql
CREATE TABLE plates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    plate       TEXT,
    confidence  REAL,
    timestamp   TEXT,
    image_path  TEXT,
    status      TEXT    -- 'NORMAL' or 'BLACKLISTED'
)
```

---

## Blacklist

Edit the `BLACKLIST` list in `api.py` to add/remove flagged plates:

```python
BLACKLIST = [
    "AEJ 7544",
    "ADT 9282",
    "ADX 3291",
    "AHG 9615"
]
```

---

## Flutter App Integration

The Flutter app sends images to the `/detect` endpoint:

```dart
var request = http.MultipartRequest(
  'POST',
  Uri.parse('https://number-plate-detection-8e4q.onrender.com/detect'),
);
request.files.add(await http.MultipartFile.fromPath('image', imagePath));
var response = await request.send();
```

---

## License

MIT
