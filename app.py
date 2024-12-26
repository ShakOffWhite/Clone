from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Инициализация приложения Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'supersecretkey'

# Инициализация базы данных
db = SQLAlchemy(app)

# Инициализация менеджера входа
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Модель доски
class Board(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tasks = db.relationship('Task', backref='board', lazy=True)

# Модель задачи
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(50), default="To Do")
    board_id = db.Column(db.Integer, db.ForeignKey('board.id'))

# Функция загрузки пользователя
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Главная страница
@app.route('/')
def index():
    return render_template('login.html')

# Регистрация пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "User already exists!"
        new_user = User(email=email, password=generate_password_hash(password, method='sha256'))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Вход пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

# Выход пользователя
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Страница пользователя с досками
@app.route('/dashboard')
@login_required
def dashboard():
    boards = Board.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', boards=boards)

# Создание новой доски
@app.route('/create_board', methods=['POST'])
@login_required
def create_board():
    board_name = request.form['name']
    new_board = Board(name=board_name, user_id=current_user.id)
    db.session.add(new_board)
    db.session.commit()
    return redirect(url_for('dashboard'))

# Просмотр доски
@app.route('/board/<int:board_id>')
@login_required
def view_board(board_id):
    board = Board.query.get_or_404(board_id)
    tasks = Task.query.filter_by(board_id=board.id).all()
    return render_template('board.html', board=board, tasks=tasks)

# Добавление новой задачи
@app.route('/add_task/<int:board_id>', methods=['POST'])
@login_required
def add_task(board_id):
    task_name = request.form['task_name']
    new_task = Task(name=task_name, board_id=board_id)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('view_board', board_id=board_id))

# Удаление задачи
@app.route('/delete_task/<int:task_id>')
@login_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(request.referrer)

# Обновление задачи
@app.route('/update_task/<int:task_id>', methods=['POST'])
@login_required
def update_task(task_id):
    task = Task.query.get(task_id)
    task.status = request.form['status']
    db.session.commit()
    return redirect(request.referrer)

# Инициализация базы данных
if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
