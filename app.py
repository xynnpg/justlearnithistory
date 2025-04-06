from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse as url_parse
from forms import LessonForm, TestForm, LoginForm
import os
import json
import datetime
import sqlite3
from datetime import timedelta
from flask import session

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
    order = db.Column(db.Integer, nullable=False)
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
    # Get lessons ordered by order, avoiding created_at column
    lessons = Lesson.query.with_entities(
        Lesson.id, 
        Lesson.title, 
        Lesson.content, 
        Lesson.order
    ).order_by(Lesson.order).all()
    return render_template('lessons.html', lessons=lessons)

@app.route('/tests')
def tests():
    try:
        tests = Test.query.all()
    except Exception as e:
        if 'no such column: test.order' in str(e):
            # If the order column doesn't exist, recreate the database
            print("Recreating database with correct schema...")
            db.drop_all()
            db.create_all()
            tests = []
        else:
            raise e
    return render_template('tests.html', tests=tests)

@app.route('/test/<int:test_id>/submit', methods=['POST'])
def submit_test(test_id):
    test = Test.query.get_or_404(test_id)
    data = request.get_json()
    answers = data.get('answers', [])
    
    questions = json.loads(test.questions_json)
    correct_answers = 0
    total_questions = len(questions)
    
    for answer in answers:
        question_index = answer.get('questionIndex')
        user_answer = answer.get('answer')
        
        if question_index < len(questions):
            question = questions[question_index]
            correct_answer = question.get('correct_answer')
            
            # Skip if either answer is None or empty
            if user_answer is None or correct_answer is None:
                continue
                
            if question.get('type') == 'multiple_choice':
                # For multiple choice, compare the string representations directly
                if str(user_answer).strip() == str(correct_answer).strip():
                    correct_answers += 1
            elif question.get('type') == 'true_false':
                # For true/false, normalize both answers
                user_ans = str(user_answer).lower().strip()
                correct_ans = str(correct_answer).lower().strip()
                
                # Handle common variations
                if user_ans in ['true', 'adevarat', 'da'] and correct_ans in ['true', 'adevarat', 'da']:
                    correct_answers += 1
                elif user_ans in ['false', 'fals', 'nu'] and correct_ans in ['false', 'fals', 'nu']:
                    correct_answers += 1
            else:  # short answer
                # For short answer, normalize both answers and do a more flexible comparison
                user_ans = str(user_answer).lower().strip()
                correct_ans = str(correct_answer).lower().strip()
                
                # Remove extra spaces and normalize
                user_ans = ' '.join(user_ans.split())
                correct_ans = ' '.join(correct_ans.split())
                
                if user_ans == correct_ans:
                    correct_answers += 1
    
    # Calculate score as a percentage of correct answers
    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # Save test result if user is logged in
    if current_user.is_authenticated:
        test_result = TestResult(
            user_id=current_user.id,
            test_id=test_id,
            answers_json=json.dumps(answers),
            score=score,
            submitted_at=datetime.datetime.now()
        )
        db.session.add(test_result)
        db.session.commit()
    
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
    # Get lessons without created_at column
    lessons = Lesson.query.with_entities(
        Lesson.id, 
        Lesson.title, 
        Lesson.content, 
        Lesson.order
    ).order_by(Lesson.order).all()
    
    # Get tests without order column
    try:
        tests = Test.query.all()
    except Exception as e:
        if 'no such column: test.order' in str(e):
            # If the order column doesn't exist, recreate the database
            print("Recreating database with correct schema...")
            db.drop_all()
            db.create_all()
            tests = []
        else:
            raise e
    
    lesson_form = LessonForm()
    test_form = TestForm()
    return render_template('admin/dashboard.html', 
                         users=users, 
                         lessons=lessons, 
                         tests=tests,
                         lesson_form=lesson_form,
                         test_form=test_form)

@app.route('/admin/lesson/add', methods=['GET', 'POST'])
@login_required
def add_lesson():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
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
@login_required
def edit_lesson(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get lesson without created_at column
    lesson = Lesson.query.with_entities(
        Lesson.id, 
        Lesson.title, 
        Lesson.content, 
        Lesson.order
    ).filter(Lesson.id == id).first_or_404()
    
    if request.method == 'POST':
        # Update lesson fields
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

@app.route('/admin/test/add', methods=['GET', 'POST'])
@login_required
def add_test():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    form = TestForm()
    if request.method == 'POST' and form.validate_on_submit():
        test = Test(
            title=form.title.data,
            order=form.order.data,
            questions_json=form.questions_json.data
        )
        db.session.add(test)
        db.session.commit()
        flash('Test added successfully!')
        return redirect(url_for('admin'))
    
    return render_template('admin/add_test.html', form=form)

@app.route('/admin/test/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_test(id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    test = Test.query.get_or_404(id)
    if request.method == 'POST':
        test.title = request.form.get('title')
        test.order = int(request.form.get('order'))
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
    
    # First delete all associated test results
    TestResult.query.filter_by(test_id=id).delete()
    
    # Then delete the test
    db.session.delete(test)
    db.session.commit()
    flash('Test deleted successfully!')
    return redirect(url_for('admin'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            # Set longer session duration for admin users
            if user.is_admin:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=30)  # 30 days for admin users
            else:
                session.permanent = True
                app.permanent_session_lifetime = timedelta(days=7)  # 7 days for regular users
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
        flash('Invalid username or password')
    return render_template('login.html', form=form)

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

@app.route('/lesson/<int:lesson_id>')
def lesson(lesson_id):
    # Get a specific lesson, avoiding created_at column
    lesson = Lesson.query.with_entities(
        Lesson.id, 
        Lesson.title, 
        Lesson.content, 
        Lesson.order
    ).filter(Lesson.id == lesson_id).first_or_404()
    return render_template('lesson.html', lesson=lesson)

@app.route('/test/<int:test_id>')
def get_test(test_id):
    test = Test.query.get_or_404(test_id)
    return jsonify({
        'id': test.id,
        'title': test.title,
        'questions': test.questions_json
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)