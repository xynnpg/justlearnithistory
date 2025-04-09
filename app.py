from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LessonForm
import os
import json
import datetime
import sqlite3
from datetime import timedelta
from flask import session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///justlearnit.db'
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)

@app.route('/')
def index():
    latest_lessons = Lesson.query.with_entities(
        Lesson.id, 
        Lesson.title, 
        Lesson.content, 
        Lesson.order
    ).order_by(Lesson.id.desc()).limit(3).all()
    return render_template('index.html', latest_lessons=latest_lessons)

@app.route('/lessons')
def lessons():
    lessons = Lesson.query.with_entities(
        Lesson.id, 
        Lesson.title, 
        Lesson.content, 
        Lesson.order
    ).order_by(Lesson.order).all()
    return render_template('lessons.html', lessons=lessons)

@app.route('/admin')
def admin():
    users = User.query.all()
    lessons = Lesson.query.with_entities(
        Lesson.id, 
        Lesson.title, 
        Lesson.content, 
        Lesson.order
    ).order_by(Lesson.order).all()
    lesson_form = LessonForm()
    return render_template('admin/dashboard.html', 
                         users=users, 
                         lessons=lessons,
                         lesson_form=lesson_form)

@app.route('/admin/lesson/add', methods=['GET', 'POST'])
def add_lesson():
    form = LessonForm()
    if request.method == 'POST' and form.validate_on_submit():
        try:
            lesson = Lesson(
                title=form.title.data,
                content=form.content.data,
                order=form.order.data,
                created_at=datetime.datetime.now()
            )
            db.session.add(lesson)
            db.session.commit()
            flash('Lesson added successfully!')
            return redirect(url_for('admin'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding lesson: {str(e)}')
            print(f"Error adding lesson: {e}")

    return render_template('admin/add_lesson.html', form=form)

@app.route('/admin/lesson/edit/<int:id>', methods=['GET', 'POST'])
def edit_lesson(id):
    lesson = Lesson.query.with_entities(
        Lesson.id, 
        Lesson.title, 
        Lesson.content, 
        Lesson.order
    ).filter(Lesson.id == id).first_or_404()

    if request.method == 'POST':
        lesson.title = request.form.get('title')
        lesson.content = request.form.get('content')
        lesson.order = int(request.form.get('order'))
        db.session.commit()
        flash('Lesson updated successfully!')
        return redirect(url_for('admin'))

    form = LessonForm(obj=lesson)
    return render_template('admin/edit_lesson.html', form=form, lesson=lesson)

@app.route('/admin/lesson/delete/<int:id>', methods=['POST'])
def delete_lesson(id):
    lesson = Lesson.query.get_or_404(id)
    db.session.delete(lesson)
    db.session.commit()
    flash('Lesson deleted successfully!')
    return redirect(url_for('admin'))

@app.route('/lesson/<int:lesson_id>')
def lesson(lesson_id):
    lesson = Lesson.query.with_entities(
        Lesson.id, 
        Lesson.title, 
        Lesson.content, 
        Lesson.order
    ).filter(Lesson.id == lesson_id).first_or_404()
    return render_template('lesson.html', lesson=lesson)

@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to filename to prevent duplicates
        filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'url': url_for('static', filename=f'images/{filename}')})
        
    return jsonify({'error': 'Invalid file type'}), 400

def init_db():
    """Initialize the database and perform any necessary migrations."""
    with app.app_context():
        db.create_all()
        try:
            Lesson.query.order_by(Lesson.created_at).first()
        except Exception as e:
            if 'no such column: lesson.created_at' in str(e):
                print("Adding created_at column to Lesson table...")
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'justlearnit.db')
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                try:
                    cursor.execute("ALTER TABLE lesson ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                    conn.commit()
                    print("Column added successfully.")
                except Exception as e:
                    print(f"Error adding column: {e}")
                finally:
                    conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)