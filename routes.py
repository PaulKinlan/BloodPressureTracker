from flask import render_template, request, redirect, url_for, flash, session
from app import app, db
from models import User, BloodPressureReading
from werkzeug.security import generate_password_hash
from sqlalchemy import desc

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Logged in successfully.')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        systolic = int(request.form['systolic'])
        diastolic = int(request.form['diastolic'])
        pulse = int(request.form['pulse']) if request.form['pulse'] else None
        notes = request.form['notes']
        
        new_reading = BloodPressureReading(
            user_id=user.id,
            systolic=systolic,
            diastolic=diastolic,
            pulse=pulse,
            notes=notes
        )
        
        db.session.add(new_reading)
        db.session.commit()
        
        flash('Blood pressure reading added successfully.')
    
    readings = BloodPressureReading.query.filter_by(user_id=user.id).order_by(desc(BloodPressureReading.timestamp)).limit(10).all()
    
    chart_data = {
        'labels': [reading.timestamp.strftime('%Y-%m-%d %H:%M') for reading in reversed(readings)],
        'systolic': [reading.systolic for reading in reversed(readings)],
        'diastolic': [reading.diastolic for reading in reversed(readings)]
    }
    
    return render_template('dashboard.html', user=user, readings=readings, chart_data=chart_data)
