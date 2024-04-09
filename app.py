from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import os
import face_recognition
import csv
from werkzeug.utils import secure_filename
app = Flask(__name__)

# Replace this path with the path to your images folder
images_path = "images"
csv_file_path = "data.csv"  # Path to the CSV file to store data

# Set the folder where you want to store the uploaded images
UPLOAD_FOLDER = images_path
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file types
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Load existing images and encode faces
existing_face_encodings = []
existing_image_files = []
existing_desired_names = []

for filename in os.listdir(images_path):
    if filename.endswith(".jpg") or filename.endswith(".png"):
        image = face_recognition.load_image_file(os.path.join(images_path, filename))
        encoding = face_recognition.face_encodings(image)[0]
        existing_face_encodings.append(encoding)
        existing_image_files.append(filename)
        existing_desired_names.append(filename.split('.')[0])  # Extract desired name from filename

# Load existing data from CSV file if it exists
if os.path.exists(csv_file_path):
    with open(csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            existing_face_encodings.append([float(val) for val in row['face_encoding'].split(',')])
            existing_desired_names.append(row['desired_name'])
            existing_image_files.append(row['image_filename'])

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
        desired_name = request.form.get('desired_name')

        if user_image.filename == '':
            return redirect(url_for('index'))

        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
                    
            # Customize the desired name (e.g., based on a form input)
            desired_name = request.form.get('desired_name', 'default_name').replace(" ","_")
            new_filename = f"{desired_name}.jpg"  # Assuming you want to save images as PNG
                    
            # Save the file with the desired name in the specified folder
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))

        # Load user image and encode faces
        user_image_data = face_recognition.load_image_file(user_image)
        user_face_encoding = face_recognition.face_encodings(user_image_data)

        if not user_face_encoding:
            return render_template('index.html', error="No face found in the uploaded image.")

        # Convert face encoding to a string for CSV storage
        face_encoding_str = ','.join(map(str, user_face_encoding[0]))

        # Append data to existing lists
        existing_face_encodings.append(user_face_encoding[0])
        existing_desired_names.append(desired_name)
        existing_image_files.append(new_filename)

        # Append data to CSV file
        with open(csv_file_path, 'a', newline='') as csvfile:
            fieldnames = ['desired_name', 'instagram_id', 'face_encoding', 'image_filename']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not os.path.exists(csv_file_path):
                writer.writeheader()
            writer.writerow({
                'desired_name': desired_name,
                'face_encoding': face_encoding_str,
                'image_filename': new_filename
            })

        return render_template('index.html', upload="Image uploaded and data stored successfully.")

    else:
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

    # Load user image and encode faces
    user_image_data = face_recognition.load_image_file(user_image)
    user_face_encoding = face_recognition.face_encodings(user_image_data)

    if not user_face_encoding:
        return jsonify(error="No face found in the uploaded image.")

    # Compare the user face with existing faces
    results = face_recognition.compare_faces(existing_face_encodings, user_face_encoding[0])

    # Determine the result
    match_index = next((index for index, result in enumerate(results) if result), None)

    if match_index is not None:
        matched_desired_name = existing_desired_names[match_index]
        matched_image_path = "/images/" + existing_image_files[match_index]

        # Return JSON data and render index page
        return render_template('index.html', success=f'Image matched successfully with {matched_desired_name.replace("_"," ")}', match=True,
                               matched_desired_name=matched_desired_name.replace("_"," "),
                               matched_image_path=matched_image_path)

    else:
        # Return JSON data and render index page
        return render_template('index.html', match=False,
                               error="No match found.")
if __name__ == '__main__':
    app.run(debug=True)
