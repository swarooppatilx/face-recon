from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import os
import face_recognition
import csv

from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
images_path = "images"
csv_file_path = "data.csv"
UPLOAD_FOLDER = images_path
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper functions
def load_existing_data():
    existing_face_encodings = []
    existing_image_files = []
    existing_desired_names = []
    existing_aadhaar_images = []

    if os.path.exists(csv_file_path):
        with open(csv_file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_face_encodings.append([float(val) for val in row['face_encoding'].split(',')])
                existing_desired_names.append(row['desired_name'])
                existing_image_files.append(row['image_filename'])
                existing_aadhaar_images.append(row['aadhaar_image_filename'])

    return existing_face_encodings, existing_image_files, existing_desired_names, existing_aadhaar_images

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/images/<path:filename>')
def static_files(filename):
    return send_from_directory('images', filename)

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/add', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        user_image = request.files['file']
        aadhaar_file = request.files['aadhaar_file']
        desired_name = request.form.get('desired_name')

        if aadhaar_file.filename == '' or user_image.filename == '':
            return redirect(request.url)

        if aadhaar_file and allowed_file(aadhaar_file.filename):
            aadhaar_filename = secure_filename(aadhaar_file.filename)
            aadhaar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], aadhaar_filename))

        if user_image and allowed_file(user_image.filename):
            filename = secure_filename(user_image.filename)
            user_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            user_image_data = face_recognition.load_image_file(user_image)
            user_face_encoding = face_recognition.face_encodings(user_image_data)

            if not user_face_encoding:
                return render_template('index.html', error="No face found in the uploaded image.")

            face_encoding_str = ','.join(map(str, user_face_encoding[0]))

            existing_face_encodings, existing_image_files, existing_desired_names, _ = load_existing_data()
            existing_face_encodings.append(user_face_encoding[0])
            existing_desired_names.append(desired_name)
            existing_image_files.append(filename)

            with open(csv_file_path, 'a', newline='') as csvfile:
                fieldnames = ['desired_name', 'instagram_id', 'face_encoding', 'image_filename', 'aadhaar_image_filename']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not os.path.exists(csv_file_path):
                    writer.writeheader()
                writer.writerow({
                    'desired_name': desired_name,
                    'face_encoding': face_encoding_str,
                    'image_filename': filename,
                    'aadhaar_image_filename': aadhaar_filename
                })

            return render_template('index.html', upload="Image uploaded and data stored successfully.")
    return render_template('add.html')

@app.route('/compare')
def compare():
    return render_template('compare.html')

@app.route('/compare-image', methods=['POST'])
def compare_image():
    if 'file' not in request.files:
        return jsonify(error="No image provided.")

    user_image = request.files['file']

    if user_image.filename == '':
        return jsonify(error="No image provided.")

    user_image_data = face_recognition.load_image_file(user_image)
    user_face_encoding = face_recognition.face_encodings(user_image_data)

    if not user_face_encoding:
        return render_template('index.html', match=False, error="No Face Found!")

    existing_face_encodings, existing_image_files, existing_desired_names, existing_aadhaar_images = load_existing_data()

    results = face_recognition.compare_faces(existing_face_encodings, user_face_encoding[0], tolerance=0.55)
    match_index = next((index for index, result in enumerate(results) if result), None)

    if match_index is not None:
        matched_desired_name = existing_desired_names[match_index]
        matched_image_path = "/images/" + existing_image_files[match_index]
        matched_aadhaar_path = "/images/" + existing_aadhaar_images[match_index]

        return render_template('index.html', success=f'Image matched successfully with {matched_desired_name.replace("_"," ")}', match=True,
                               matched_desired_name=matched_desired_name.replace("_"," "),
                               matched_image_path=matched_image_path, matched_aadhaar_path=matched_aadhaar_path)
    else:
        return render_template('index.html', match=False, error="No match found.")

if __name__ == '__main__':
    app.run(debug=True)
