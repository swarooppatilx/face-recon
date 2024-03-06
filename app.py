from flask import Flask, render_template, request, redirect, url_for
import face_recognition
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/add')
def add():
    return render_template('add.html')

@app.route('/compare', methods=['POST'])
def compare():
    
    # Replace these paths with the paths to your existing images
    existing_images_path = "images"

    # Load existing images and encode faces
    existing_face_encodings = []
    existing_image_files = []



    for filename in os.listdir(existing_images_path):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            image = face_recognition.load_image_file(os.path.join(existing_images_path, filename))
            encoding = face_recognition.face_encodings(image)[0]
            existing_face_encodings.append(encoding)
            existing_image_files.append(filename)

    if 'file' not in request.files:
        return redirect(url_for('index'))

    user_image = request.files['file']

    if user_image.filename == '':
        return redirect(url_for('index'))

    # Load user image and encode faces
    user_image_data = face_recognition.load_image_file(user_image)
    user_face_encoding = face_recognition.face_encodings(user_image_data)

    if not user_face_encoding:
        return render_template('index.html', error="No face found in the uploaded image.")

    # Compare the user face with existing faces
    results = face_recognition.compare_faces(existing_face_encodings, user_face_encoding[0])

    # Determine the result
    match_index = next((index for index, result in enumerate(results) if result), None)

    if match_index is not None:
        matched_filename = existing_image_files[match_index]
        return render_template('index.html', match=True, matched_filename=matched_filename)
    else:
        return render_template('index.html', match=False)
    

# Set the folder where you want to store the uploaded images
UPLOAD_FOLDER = 'images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file types
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check if the file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        # Use secure_filename to ensure safe filenames
        original_filename = secure_filename(file.filename)
        
        # Get the desired name from the form input
        desired_name = request.form.get('desired_name', 'default_name')
        
        # Construct the new filename using the desired name and original extension
        filename = f"{desired_name}.{original_filename.rsplit('.', 1)[1].lower()}"
        
        # Save the file in the specified folder
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Redirect to the index page with the filename as a parameter
        return redirect(url_for('index', filename=filename))

    return redirect(request.url)

if __name__ == '__main__':
    app.run(debug=True)