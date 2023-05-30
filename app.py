from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# mysql config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'batiksnap'
mysql = MySQL(app)

# @app.route('/')
# def root():
#     return 'halo ini flask'

# @app.route('/siswa')
# def siswa():
#     return jsonify({'name' : 'figih'})

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
        return jsonify({'message': 'data added successfully'})
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
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Invalid password'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50, debug=True)