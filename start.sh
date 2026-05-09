#!/bin/bash

# Download YOLO model weights if not present
MODEL_PATH="runs/detect/train/weights/best.pt"

if [ ! -f "$MODEL_PATH" ]; then
    echo "==> Downloading YOLO model weights..."
    mkdir -p runs/detect/train/weights
    FILE_ID="1z_Fs9HmlaCjB0OOpRxXUovwv-IiMT4ME"
    wget --no-check-certificate \
        "https://drive.usercontent.google.com/download?id=${FILE_ID}&export=download&confirm=t" \
        -O "$MODEL_PATH"
    echo "==> Model downloaded. Size: $(du -sh $MODEL_PATH)"
else
    echo "==> Model already exists, skipping download."
fi

# Start the app with longer timeout for model loading
exec gunicorn api:app --timeout 120 --workers 1
