from flask import Flask, jsonify, request
import tensorflow as tf
import numpy as np
import os
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import  img_to_array, load_img
from flask_mysqldb import MySQL
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# mysql config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'batiksnap'
app.config['JWT_SECRET_KEY'] = 'batiksnap'
jwt = JWTManager(app)
mysql = MySQL(app)

UPLOAD_FOLDER = 'img'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

model = load_model('model.h5')

def load_label(path):
  with open(path, "r") as f:
    lines = f.read()
    motives_list = lines.strip().split("\n")
    return motives_list

motives_list = load_label("label.txt")

def predict(path):
    motives_list
    img = load_img(path, target_size=(224, 224, 3))
    img_array = img_to_array(img) / 255.0
    img_array = tf.expand_dims(img_array, 0)
    prediction = model.predict(img_array,verbose = 0)
    pred_idx = np.argmax(prediction)
    pred_motive = motives_list[pred_idx]
    pred_confidence = prediction[0][pred_idx] * 100

    return pred_motive

def create_list_data(result):
        
        cursor = mysql.connection.cursor()
        sql = "SELECT id, nama, image, deskripsi FROM batik where nama LIKE %s"
        val = (result, )
        cursor.execute(sql, val)

        # get column names from cursor description
        column_names =  [i[0] for i in cursor.description]
        # fetch data and format into list dictionaries
        data = []
        for row in cursor.fetchall():
            data.append(dict(zip(column_names, row)))
            # console.log()
        return data
        cursor.close()
        

@app.route('/batik', methods=['GET'])
def batik():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM batik")
    # get column names from cursor description
    column_names =  [i[0] for i in cursor.description]
    # fetch data and format into list dictionaries
    data = []
    for row in cursor.fetchall():
        data.append(dict(zip(column_names, row)))
        # console.log()
        return jsonify(data)
    cursor.close()
    
@app.route('/register', methods=['POST'])
def register():
    # get data
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # check data
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
        user = cursor.fetchone()
        cursor.close()  

        if user:
            return jsonify({'message': 'user already exists'}), 409
    
        # Membuat hash dari password
        hashed_password = generate_password_hash(password)

        # query sql
        cursor = mysql.connection.cursor()
        sql = "INSERT INTO users (name, email, password) VALUES (%s,%s,%s)"
        val = (name, email, hashed_password)
        cursor.execute(sql, val)

        mysql.connection.commit()
        access_token = create_access_token(identity=email)
        return jsonify({'message': 'data added successfully', 'access_token': access_token})
        cursor.close()

@app.route('/login', methods=['POST'])
def login():
    # Mengambil data dari request
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Mengecek apakah username ada di database
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    users = cursor.fetchone()
    cursor.close()
    
    if not users:
        return jsonify({'message': 'Invalid email'}), 401
    
    # Memeriksa kecocokan password
    if check_password_hash(users[4], password):
        # create access token
        access_token = create_access_token(identity=email)
        return jsonify({'message': 'Login successful', 'access_token': access_token})
    else:
        return jsonify({'message': 'Invalid password'}), 401

@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # Clear the access token cookie
    response = jsonify({'message': 'Logged out successfully'})
    unset_jwt_cookies(response)
    return response

@app.route('/upload', methods=['POST', 'GET'])
@jwt_required()
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'true' ,'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({ 'error': 'true' ,'message': 'No file selected'}), 400    
    
    # Simpan file pada direktori lokal
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

    # Dapatkan URL file yang diunggah
    file_url = f"{UPLOAD_FOLDER}/{file.filename}"

    result_predict = predict(file_url)
    data = create_list_data(result_predict)

    return jsonify({'error': 'false' ,'predict' : result_predict, 'listBatik' : data})

@app.route('/detail/<int:id>', methods=['GET'])
@jwt_required()
def get_batik_data(id):
        cursor = mysql.connection.cursor()
        sql = "SELECT * FROM batik where id = %s"
        val = (id, )
        cursor.execute(sql, val)

        # get column names from cursor description
        column_names =  [i[0] for i in cursor.description]
        # fetch data and format into list dictionaries
        data = []
        for row in cursor.fetchall():
            data.append(dict(zip(column_names, row)))
            # console.log()
        cursor.close()
        return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50, debug=True)