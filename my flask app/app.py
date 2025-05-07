from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import mysql.connector
from mysql.connector import Error
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from werkzeug.security import check_password_hash  # For secure password verification

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace this with a secure key

# MySQL Database connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='medical_db',
            user='root',
            password='B31162298m#2002'
        )
        return conn
    except Error as e:
        print(f"Error: {e}")
        return None

# Function to generate PDF
def generate_pdf(data):
    pdf_buffer = BytesIO()
    p = canvas.Canvas(pdf_buffer, pagesize=letter)
    
    p.drawString(100, 750, "Prescription")
    p.drawString(100, 730, f"Patient ID: {data['patient_id']}")
    p.drawString(100, 710, f"Diagnosis: {data['diagnosis']}")
    p.drawString(100, 690, f"Medications: {data['medications']}")
    p.drawString(100, 670, f"Dosage: {data['dosage']}")
    
    p.showPage()
    p.save()
    pdf_buffer.seek(0)
    return pdf_buffer

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Debugging: Print form data to verify
        print(f"Username: {username}")
        print(f"Password: {password}")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Fetch the user from the database
        cursor.execute('SELECT * FROM users WHERE username=%s', (username,))
        user = cursor.fetchone()
        
        if user:
            # Check if the entered password matches the stored hashed password
            if check_password_hash(user['password'], password):  # Use hash comparison
                session['username'] = username  # Set the session for the logged-in user
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect password')  # Incorrect password
        else:
            flash('User not found')  # User not found
        
        cursor.close()
        conn.close()
    
    return render_template('login.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM patients')
    patients = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('dashboard.html', patients=patients)

# Route to add a new patient
@app.route('/add_patient', methods=['POST'])
def add_patient():
    if 'username' not in session:
        return redirect(url_for('login'))

    name = request.form['name']
    symptoms = request.form['symptoms']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO patients (patient_name, symptoms) VALUES (%s, %s)', (name, symptoms))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('dashboard'))

# Generate prescription route
@app.route('/generate_prescription', methods=['GET', 'POST'])
def generate_prescription():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        diagnosis = request.form['diagnosis']
        medications = request.form['medications']
        dosage = request.form['dosage']
        
        pdf = generate_pdf({
            'patient_id': patient_id,
            'diagnosis': diagnosis,
            'medications': medications,
            'dosage': dosage
        })
        
        return send_file(pdf, as_attachment=True, download_name='prescription.pdf', mimetype='application/pdf')
    
    return render_template('generate_prescription.html')

# Prescription history route
@app.route('/prescription_history')
def prescription_history():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT p.id, pat.patient_name, p.diagnosis, p.medications, p.dosage, p.instructions, p.date_issued
        FROM prescriptions p
        JOIN patients pat ON p.patient_id = pat.id
        ORDER BY p.date_issued DESC
    ''')
    prescriptions = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('prescription_history.html', prescriptions=prescriptions)

# Suggest prescription route based on symptoms
@app.route('/suggest_prescription', methods=['GET', 'POST'])
def suggest_prescription():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    suggestions = []
    if request.method == 'POST':
        symptoms = request.form['symptoms']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''  
            SELECT diagnosis, medications, dosage
            FROM symptom_based_prescriptions
            WHERE symptoms LIKE %s
        ''', (f'%{symptoms}%',))
        suggestions = cursor.fetchall()
        cursor.close()
        conn.close()
    
    return render_template('suggest_prescription.html', suggestions=suggestions)

# Forgot password route
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    return render_template('forgot_password.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
