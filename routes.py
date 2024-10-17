from flask import render_template, request, redirect, url_for, flash, session
from app import app, db
from models import User, BloodPressureReading
from werkzeug.security import generate_password_hash
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
import re
from datetime import timedelta, datetime

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
        confirm_password = request.form['confirm_password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        date_of_birth = request.form['date_of_birth']
        preferred_unit = request.form['preferred_unit']
        
        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('register'))
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long.')
            return redirect(url_for('register'))
        
        if not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password):
            flash('Password must contain at least one uppercase letter, one lowercase letter, and one number.')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('register'))
        
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d').date() if date_of_birth else None,
            preferred_unit=preferred_unit
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. Please log in.')
            return redirect(url_for('login'))
        except IntegrityError as e:
            db.session.rollback()
            if 'user_email_key' in str(e):
                flash('Email address already registered. Please use a different email.')
            else:
                flash('An error occurred during registration. Please try again.')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            if remember:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)
            flash('Logged in successfully.')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
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

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.email = request.form['email']
        user.preferred_unit = request.form['preferred_unit']
        
        date_of_birth = request.form['date_of_birth']
        if date_of_birth:
            user.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        
        try:
            db.session.commit()
            flash('Profile updated successfully.')
        except IntegrityError:
            db.session.rollback()
            flash('An error occurred while updating your profile. Please try again.')
    
    return render_template('profile.html', user=user)