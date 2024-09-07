from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<User{self.username}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('quizzes', lazy=True))

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(150), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    quiz = db.relationship('Quiz', backref=db.backref('questions', lazy=True))

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(150), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    question = db.relationship('Question', backref=db.backref('options', lazy=True))

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    user = db.relationship('User', backref=db.backref('results', lazy=True))
    quiz = db.relationship('Quiz', backref=db.backref('results', lazy=True))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password, is_admin=True)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('admin_login'))
    return render_template('admin_register.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password) and user.is_admin:
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials or not an admin user.', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html', username=session['username'])

@app.route('/admin/manage_quizzes', methods=['GET', 'POST'])
def manage_quizzes():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    categories = Category.query.all()
    quizzes = Quiz.query.all()
    if request.method == 'POST':
        name = request.form['name']
        category_id = request.form['category_id']
        new_quiz = Quiz(name=name, category_id=category_id)
        db.session.add(new_quiz)
        db.session.commit()
        flash('Quiz added successfully!', 'success')
        return redirect(url_for('manage_quizzes'))
    return render_template('manage_quizzes.html', categories=categories, quizzes=quizzes)

@app.route('/admin/delete_quiz/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    quiz = Quiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted successfully!', 'success')
    return redirect(url_for('manage_quizzes'))

@app.route('/admin/manage_categories', methods=['GET', 'POST'])
def manage_categories():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    categories = Category.query.all()
    if request.method == 'POST':
        name = request.form['category']
        new_category = Category(name=name)
        db.session.add(new_category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('manage_categories'))
    return render_template('manage_categories.html', categories=categories)

@app.route('/admin/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    category = Category.query.get_or_404(category_id)
    
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('manage_categories'))

@app.route('/admin/manage_questions/<int:quiz_id>', methods=['GET', 'POST'])
def manage_questions(quiz_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    if request.method == 'POST':
        text = request.form['text']
        new_question = Question(text=text, quiz_id=quiz_id)
        db.session.add(new_question)
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('manage_questions', quiz_id=quiz_id))
    return render_template('manage_questions.html', questions=questions, quiz_id=quiz_id)

@app.route('/admin/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('manage_questions', quiz_id=quiz_id))

@app.route('/admin/manage_options/<int:question_id>', methods=['GET', 'POST'])
def manage_options(question_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    question = Question.query.get_or_404(question_id)
    options = Option.query.filter_by(question_id=question_id).all()
    if request.method == 'POST':
        text = request.form['text']
        is_correct = 'is_correct' in request.form
        new_option = Option(text=text, is_correct=is_correct, question_id=question_id)
        db.session.add(new_option)
        db.session.commit()
        flash('Option added successfully!', 'success')
        return redirect(url_for('manage_options', question_id=question_id))
    return render_template('manage_options.html', question=question, options=options)

@app.route('/admin/delete_option/<int:option_id>', methods=['POST'])
def delete_option(option_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    option = Option.query.get_or_404(option_id)
    question_id = option.question_id
    db.session.delete(option)
    db.session.commit()
    flash('Option deleted successfully!', 'success')
    return redirect(url_for('manage_options', question_id=question_id))

@app.route('/student/register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('student_login'))
    return render_template('student_register.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('student_login.html')

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('student_login'))
    quizzes = Quiz.query.all()
    return render_template('student_dashboard.html', username=session['username'], quizzes=quizzes)

@app.route('/student/attempt_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def attempt_quiz(quiz_id):
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('student_login'))
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    if request.method == 'POST':
        score = 0
        for question in questions:
            user_answer = request.form.get(f'answer_{question.id}')
            correct_option = Option.query.filter_by(question_id=question.id, is_correct=True).first()
            if correct_option and user_answer == correct_option.text:
                score += 1
        result = Result(user_id=session['user_id'], quiz_id=quiz.id, score=score)
        db.session.add(result)
        db.session.commit()
        flash(f'Quiz submitted successfully! Your score is {score}/{len(questions)}', 'success')
        return redirect(url_for('student_dashboard'))
    return render_template('attempt_quiz.html', quiz=quiz, questions=questions)


@app.route('/student/view_results')
def view_results():
    if 'user_id' not in session or session.get('is_admin'):
        return redirect(url_for('student_login'))
    results = Result.query.filter_by(user_id=session['user_id']).all()
    return render_template('view_results.html', results=results)

@app.route('/admin/logout')
def admin_logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect(url_for('admin_login'))


@app.route('/student/logout')
def student_logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect(url_for('student_login'))

@app.route('/leaderboard')
def leaderboard():
    users = User.query.all()
    quizzes = Quiz.query.all()
    return render_template('leaderboard.html', users=users, quizzes=quizzes)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/view_leaderboard', methods=['GET'])
def view_leaderboard():
    user_id = request.args.get('user_id')
    quiz_id = request.args.get('quiz_id')
    leaderboard_results = Result.query

    if user_id:
        leaderboard_results = leaderboard_results.filter_by(user_id=user_id)
    if quiz_id:
        leaderboard_results = leaderboard_results.filter_by(quiz_id=quiz_id)

    leaderboard_results = leaderboard_results.order_by(Result.score.desc()).all()
    users = User.query.all()
    quizzes = Quiz.query.all()

    return render_template('leaderboard.html', leaderboard_results=leaderboard_results, users=users, quizzes=quizzes)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)