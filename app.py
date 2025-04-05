from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LessonForm, TestForm
import os
import json
import datetime
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///justlearnit.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
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

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    questions_json = db.Column(db.Text, nullable=False)
    
    def get_questions(self):
        return json.loads(self.questions_json)
    
    def set_questions(self, questions):
        self.questions_json = json.dumps(questions)

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    answers_json = db.Column(db.Text, nullable=False)
    score = db.Column(db.Float, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False)
    
    user = db.relationship('User', backref=db.backref('test_results', lazy=True))
    test = db.relationship('Test', backref=db.backref('test_results', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    # Get lessons ordered by id
    latest_lessons = Lesson.query.with_entities(
        Lesson.id, 
        Lesson.title, 
        Lesson.content, 
        Lesson.order
    ).order_by(Lesson.id.desc()).limit(3).all()
    return render_template('index.html', latest_lessons=latest_lessons)

@app.route('/lessons')
def lessons():
    lessons = Lesson.query.order_by(Lesson.order).all()
    return render_template('lessons.html', lessons=lessons)

@app.route('/tests')
def tests():
    tests = Test.query.all()
    return render_template('tests.html', tests=tests)

@app.route('/test/<int:test_id>/submit', methods=['POST'])
def submit_test(test_id):
    test = Test.query.get_or_404(test_id)
    data = request.get_json()
    answers = data.get('answers', [])
    
    questions = test.get_questions()
    correct_answers = 0
    total_questions = len(questions)
    
    for answer in answers:
        question_index = answer.get('questionIndex')
        user_answer = answer.get('answer')
        
        if question_index < len(questions):
            question = questions[question_index]
            correct_answer = question.get('correct_answer')
            
            if question.get('type') == 'multiple_choice':
                if str(user_answer) == str(correct_answer):
                    correct_answers += 1
            elif question.get('type') == 'true_false':
                if str(user_answer).lower() == str(correct_answer).lower():
                    correct_answers += 1
            else:  # short answer
                if str(user_answer).strip().lower() == str(correct_answer).strip().lower():
                    correct_answers += 1
    
    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    return jsonify({
        'score': score,
        'correct_answers': correct_answers,
        'total_questions': total_questions
    })

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    users = User.query.all()
    lessons = Lesson.query.all()
    tests = Test.query.all()
    lesson_form = LessonForm()
    test_form = TestForm()
    return render_template('admin/dashboard.html', 
                         users=users, 
                         lessons=lessons, 
                         tests=tests,
                         lesson_form=lesson_form,
                         test_form=test_form)

@app.route('/admin/lesson/add', methods=['POST'])
@login_required
def add_lesson():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    form = LessonForm()
    if form.validate_on_submit():
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
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding lesson: {str(e)}')
            print(f"Error adding lesson: {e}")
    return redirect(url_for('admin'))

@app.route('/admin/lesson/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_lesson(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    lesson = Lesson.query.get_or_404(id)
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
@login_required
def delete_lesson(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    lesson = Lesson.query.get_or_404(id)
    db.session.delete(lesson)
    db.session.commit()
    flash('Lesson deleted successfully!')
    return redirect(url_for('admin'))

@app.route('/admin/test/add', methods=['POST'])
@login_required
def add_test():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    form = TestForm()
    if form.validate_on_submit():
        test = Test(
            title=form.title.data,
            questions_json=form.questions_json.data
        )
        db.session.add(test)
        db.session.commit()
        flash('Test added successfully!')
    return redirect(url_for('admin'))

@app.route('/admin/test/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_test(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    test = Test.query.get_or_404(id)
    if request.method == 'POST':
        test.title = request.form.get('title')
        test.questions_json = request.form.get('questions_json')
        db.session.commit()
        flash('Test updated successfully!')
        return redirect(url_for('admin'))
    
    form = TestForm(obj=test)
    return render_template('admin/edit_test.html', form=form, test=test)

@app.route('/admin/test/delete/<int:id>', methods=['POST'])
@login_required
def delete_test(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    test = Test.query.get_or_404(id)
    db.session.delete(test)
    db.session.commit()
    flash('Test deleted successfully!')
    return redirect(url_for('admin'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user)
            return redirect(url_for('admin' if user.is_admin else 'index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

def init_db():
    """Initialize the database and perform any necessary migrations."""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if we need to add the created_at column to the Lesson table
        try:
            # Try to select from the created_at column
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