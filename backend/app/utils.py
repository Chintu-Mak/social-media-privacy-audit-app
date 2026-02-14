# backend/app/utils.py
import cv2
import numpy as np
from PIL import Image
import exifread

def extract_exif(file_bytes):
    """Extract EXIF metadata, including GPS if present."""
    exif_data = exifread.process_file(file_bytes, details=False)
    gps_info = {}

    # Extract GPS coordinates if available
    if "GPS GPSLatitude" in exif_data and "GPS GPSLongitude" in exif_data:
        lat_values = exif_data["GPS GPSLatitude"].values
        lon_values = exif_data["GPS GPSLongitude"].values
        lat_ref = exif_data.get("GPS GPSLatitudeRef")
        lon_ref = exif_data.get("GPS GPSLongitudeRef")

        def to_deg(value):
            d, m, s = [float(x.num) / float(x.den) for x in value]
            return d + (m / 60.0) + (s / 3600.0)

        lat = to_deg(lat_values)
        lon = to_deg(lon_values)
        if lat_ref and lat_ref.values != "N":
            lat = -lat
        if lon_ref and lon_ref.values != "E":
            lon = -lon

        gps_info = {"latitude": lat, "longitude": lon}

    return {"gps": gps_info if gps_info else None}


def detect_faces_and_blur(pil_image):
    """Detect faces and apply optional blurring (returns count and blur map)."""
    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

    # Load OpenCV's pretrained Haar Cascade face detector
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    blur_info = []
    for (x, y, w, h) in faces:
        face_roi = cv_image[y:y+h, x:x+w]
        blur_score = cv2.Laplacian(face_roi, cv2.CV_64F).var()

        # Convert numpy types to Python native
        blur_info.append({
            "x": int(x),
            "y": int(y),
            "w": int(w),
            "h": int(h),
            "blur_score": float(blur_score)
        })

    # ✅ Convert numpy.int32 → Python int explicitly
    face_count = int(len(faces))

    return face_count, blur_info
