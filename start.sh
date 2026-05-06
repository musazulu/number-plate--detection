#!/bin/bash

# Download YOLO model weights if not present
MODEL_PATH="runs/detect/train/weights/best.pt"

if [ ! -f "$MODEL_PATH" ]; then
    echo "==> Downloading YOLO model weights..."
    mkdir -p runs/detect/train/weights
    python -c "
import gdown
gdown.download(id='1z_Fs9HmlaCjB0OOpRxXUovwv-IiMT4ME', output='$MODEL_PATH', quiet=False)
"
    echo "==> Model downloaded successfully."
else
    echo "==> Model already exists, skipping download."
fi

# Start the app
exec gunicorn api:app
