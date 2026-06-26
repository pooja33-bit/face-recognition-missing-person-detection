from flask import Flask, render_template, url_for, request
import sqlite3
from image_dataset import create_dataset
from recognition_image import Recognition
from recognition_video import Recognition_video
import os
from werkzeug.utils import secure_filename
connection = sqlite3.connect('user_data.db')
cursor = connection.cursor()

command = """CREATE TABLE IF NOT EXISTS user(name TEXT, password TEXT, mobile TEXT, email TEXT)"""
cursor.execute(command)

command = """CREATE TABLE IF NOT EXISTS records(file TEXT, name TEXT, age TEXT, dob TEXT, gender TEXT, md TEXT)"""
cursor.execute(command)
# Configuration for file uploads
UPLOAD_FOLDER = 'static/test'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/matching', methods = ['POST', 'GET'])
def matching():
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'file' not in request.files:
                return render_template('matching.html', msg="No file selected!")
            
            file = request.files['file']
            
            # Check if file is empty
            if file.filename == '':
                return render_template('matching.html', msg="No file selected!")
            
            # Check if file type is allowed
            if not allowed_file(file.filename):
                return render_template('matching.html', msg="Invalid file type! Please upload an image file.")
            
            if file and allowed_file(file.filename):
                # Create temp filename for matching
                temp_filename = f"temp_matching_{file.filename}"
                temp_filepath = os.path.join(UPLOAD_FOLDER, temp_filename)
                
                # Save the uploaded file temporarily
                file.save(temp_filepath)
                
                # Verify file exists
                if not os.path.exists(temp_filepath):
                    return render_template('matching.html', msg="Error saving file!")
                
                # Use the temp file for recognition
                res = Recognition(temp_filepath.replace('\\', '/'))
                
                # Clean up temp file
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
                
                if res == 'unknown':
                    return render_template('matching.html', msg="Records not found on this face")  
                else:
                    connection = sqlite3.connect('user_data.db')
                    cursor = connection.cursor()
                    cursor.execute("select * from records where name = ?", (res,))
                    result = cursor.fetchone()
                    connection.close()
                    print(result)
                    return render_template('matching.html', result=result)
                    
        except Exception as e:
            print(f"Matching error: {str(e)}")
            return render_template('matching.html', msg=f"An error occurred: {str(e)}")

    return render_template('matching.html')

@app.route('/video', methods = ['POST', 'GET'])
def video():
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'file' not in request.files:
                return render_template('matching.html', msg="No file selected!")
            
            file = request.files['file']
            
            # Check if file is empty
            if file.filename == '':
                return render_template('matching.html', msg="No file selected!")
            
            # For video files, allow video extensions
            video_extensions = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'}
            if not (file and '.' in file.filename and 
                    file.filename.rsplit('.', 1)[1].lower() in video_extensions):
                return render_template('matching.html', msg="Invalid file type! Please upload a video file.")
            
            # Create temp filename for video matching
            temp_filename = f"temp_video_{file.filename}"
            temp_filepath = os.path.join(UPLOAD_FOLDER, temp_filename)
            
            # Save the uploaded video temporarily
            file.save(temp_filepath)
            
            # Verify file exists
            if not os.path.exists(temp_filepath):
                return render_template('matching.html', msg="Error saving video file!")
            
            # Use the temp file for video recognition
            res = Recognition_video(temp_filepath.replace('\\', '/'))
            
            # Clean up temp file
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            
            if res == 'unknown':
                return render_template('matching.html', msg="Records not found on this face")  
            else:
                connection = sqlite3.connect('user_data.db')
                cursor = connection.cursor()
                cursor.execute("select * from records where name = ?", (res,))
                result = cursor.fetchone()
                connection.close()
                return render_template('matching.html', result=result)
                
        except Exception as e:
            print(f"Video matching error: {str(e)}")
            return render_template('matching.html', msg=f"An error occurred: {str(e)}")

    return render_template('matching.html')

@app.route('/live')
def live():
    res = Recognition_video(0)
    if res == 'unknown':
        return render_template('matching.html', msg="records not found on this face")  
    else:
        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()
        cursor.execute("select * from records where name = '"+res+"'")
        result = cursor.fetchone()
        return render_template('matching.html', result=result)

@app.route('/details', methods = ['POST', 'GET'])
def details():
    if request.method == 'POST':
        file = request.form['file']

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()
        cursor.execute("select * from records where name = '"+file+"'")
        result = cursor.fetchone()
        if result:
            return render_template('details.html', result=result) 
        else:
            return render_template('details.html', msg='resords not found on this name') 
    return render_template('details.html')

@app.route('/upload', methods = ['POST', 'GET'])
def upload():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            age = request.form.get('age')
            dob = request.form.get('dob')
            gender = request.form.get('gender')
            md = request.form.get('md')
            
            # Validate form data
            if not all([name, age, dob, gender, md]):
                return render_template('upload.html', msg="All fields are required!")
            
            # Check if file was uploaded
            if 'file' not in request.files:
                return render_template('upload.html', msg="No file selected!")
            
            file = request.files['file']
            
            # Check if file is empty
            if file.filename == '':
                return render_template('upload.html', msg="No file selected!")
            
            # Check if file type is allowed
            if not allowed_file(file.filename):
                return render_template('upload.html', msg="Invalid file type! Please upload an image file.")
            
            if file and allowed_file(file.filename):
                # Create upload directory if it doesn't exist
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                # Create filename from name (secure)
                filename = secure_filename(name.lower().replace(' ', '_'))
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                full_filename = f"{filename}.{file_extension}"
                
                # Save file path
                filepath = os.path.join(UPLOAD_FOLDER, full_filename)
                
                # Save the file
                file.save(filepath)
                
                # Verify file was saved
                if not os.path.exists(filepath):
                    return render_template('upload.html', msg="Error saving file!")
                
                print(f"File saved successfully: {filepath}")
                
                # Convert Windows path to forward slashes and use full path with extension
                dataset_path = filepath.replace('\\', '/')
                
                print(f"Creating dataset with full path: {dataset_path}")
                print(f"Form data: name={name}, age={age}, dob={dob}, gender={gender}, md={md}")
                
                # Verify file exists and can be read before calling create_dataset
                import cv2
                test_img = cv2.imread(dataset_path)
                if test_img is None:
                    return render_template('upload.html', msg="Error: Cannot read the uploaded image file")
                
                print(f"Image loaded successfully: {test_img.shape}")
                
                # If your create_dataset function expects path without extension, 
                # pass the base path, otherwise use the full path
                try:
                    # First try with full path (recommended)
                    res = create_dataset(dataset_path, name)
                except:
                    # If that fails, try with base path (your original approach)
                    base_path = os.path.join(UPLOAD_FOLDER, filename).replace('\\', '/')
                    res = create_dataset(base_path, name)
                
                if res == 'found':
                    # Prepare values for database insertion
                    # Note: Using filename for the file field in database
                    print(f"\n\n\n\n\n{full_filename}\n\n\n\n")
                    values = [full_filename, name, age, dob, gender, md]
                    
                    connection = sqlite3.connect('user_data.db')
                    cursor = connection.cursor()
                    cursor.execute("insert into records values(?,?,?,?,?,?)", values)
                    connection.commit()
                    connection.close()

                    return render_template('upload.html', msg="Data uploaded successfully")   
                else:
                    # Remove the uploaded file if face detection failed
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return render_template('upload.html', msg="Face not found in the uploaded image")
                
        except Exception as e:
            print(f"Upload error: {str(e)}")
            return render_template('upload.html', msg=f"An error occurred: {str(e)}")
    
    return render_template('upload.html')

@app.route('/userlog', methods=['GET', 'POST'])
def userlog():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        name = request.form['name']
        password = request.form['password']

        query = "SELECT name, password FROM user WHERE name = '"+name+"' AND password= '"+password+"'"
        cursor.execute(query)

        result = cursor.fetchall()

        if result:
            return render_template('userlog.html')
        else:
            return render_template('index.html', msg='Sorry, Incorrect Credentials Provided,  Try Again')

    return render_template('index.html')


@app.route('/userreg', methods=['GET', 'POST'])
def userreg():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        name = request.form['name']
        password = request.form['password']
        mobile = request.form['phone']
        email = request.form['email']
        
        print(name, mobile, email, password)

        command = """CREATE TABLE IF NOT EXISTS user(name TEXT, password TEXT, mobile TEXT, email TEXT)"""
        cursor.execute(command)

        cursor.execute("INSERT INTO user VALUES ('"+name+"', '"+password+"', '"+mobile+"', '"+email+"')")
        connection.commit()

        return render_template('index.html', msg='Successfully Registered')
    
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('userlog.html')

@app.route('/logout')
def logout():
    return render_template('index.html')
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
