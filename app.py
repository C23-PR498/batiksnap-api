from flask import Flask, jsonify, request
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

# model = load_model('batik_pattern_recognizer_9708_8750_InceptionV3')

# def predict(path):
def get_batik_data(result_predict):
    if 'id' in request.args: 
        cursor = mysql.connection.cursor()
        sql = ("SELECT * FROM batik where id = %s")
        val = (request.args['id'],)
        cursor.execute(sql, val)

        # get column names from cursor description
        column_names =  [i[0] for i in cursor.description]
        # fetch data and format into list dictionaries
        data = []
        for row in cursor.fetchall():
            data.append(dict(zip(column_names, row)))
            # console.log(mahasiswa)
        return jsonify(data)
        
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
        # console.log(mahasiswa)
        return jsonify(data)
    cursor.close()
    
@app.route('/register', methods=['POST'])
def register():
    # get data
        name = request.json['name']
        email = request.json['email']
        password = request.json['password']

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
    email = request.json['email']
    password = request.json['password']
    
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

@app.route('/upload', methods=['POST'])
@jwt_required()  # user must be logged in to access this route
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400    
    
    # Simpan file pada direktori lokal
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

    # Dapatkan URL file yang diunggah
    file_url = f"{request.host_url}{UPLOAD_FOLDER}/{file.filename}"
    # result_predict = predict(file_url)
    # data = get_batik_data(result_predict)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50, debug=True)