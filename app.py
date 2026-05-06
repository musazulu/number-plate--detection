from flask import Flask, render_template, send_from_directory
import sqlite3

app = Flask(__name__)

# -------------------------------
# GET DATA
# -------------------------------
def get_plates():
    conn = sqlite3.connect("plates.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT plate, confidence, timestamp, image_path, status
        FROM plates 
        ORDER BY id DESC
        LIMIT 50
    """)

    data = cursor.fetchall()
    conn.close()
    return data

# -------------------------------
# SERVE IMAGES
# -------------------------------
@app.route('/snapshots/<path:filename>')
def snapshots(filename):
    return send_from_directory('snapshots', filename)

# -------------------------------
# ROUTE
# -------------------------------
@app.route("/")
def home():
    plates = get_plates()
    return render_template("index.html", plates=plates)

# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)