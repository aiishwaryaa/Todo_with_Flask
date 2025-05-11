from flask import Flask, render_template, request, redirect, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

app = Flask(__name__)
app.secret_key = "your_unique_and_secure_secret_key_here"  # Secret key added
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Todo Model
class Todo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    desc = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"{self.title} - {self.sno}"

# User Model for authentication
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Create the database and tables
with app.app_context():
    db.create_all()

# Home Route
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'user_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        todo = Todo(title=title, desc=desc)
        db.session.add(todo)
        db.session.commit()
    
    query = request.args.get('query', '').strip()  # Search query
    if query:
        search_results = Todo.query.filter(
            (Todo.title.ilike(f'%{query}%')) | (Todo.desc.ilike(f'%{query}%'))
        ).all()
    else:
        search_results = Todo.query.all()

    return render_template('index.html', alltodo=search_results, query=query)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("All fields are required!", "warning")
            return redirect('/login')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("Login successful!", "success")
            return redirect('/')
        else:
            flash("Invalid username or password!", "danger")
            return redirect('/login')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate fields
        if not username or not password or not confirm_password:
            flash("All fields are required!", "warning")
            return redirect('/register')

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect('/register')

        if len(password) < 6:
            flash("Password must be at least 6 characters long!", "warning")
            return redirect('/register')

        # Check if username exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists!", "danger")
            return redirect('/register')

        # Save the user
        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect('/login')

    return render_template('register.html')

# About Route
@app.route('/about')
def about():
    return render_template('about.html')

# Delete Route
@app.route('/delete/<int:sno>')
def delete(sno):
    if 'user_id' not in session:
        return redirect('/login')
    todo = Todo.query.filter_by(sno=sno).first()
    if todo:
        db.session.delete(todo)
        db.session.commit()
    return redirect('/')

# Update Route
@app.route('/update/<int:sno>', methods=['GET', 'POST'])
def update(sno):
    if 'user_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        todo = Todo.query.filter_by(sno=sno).first()
        todo.title = title
        todo.desc = desc
        db.session.add(todo)
        db.session.commit()
        return redirect('/')
    
    todo = Todo.query.filter_by(sno=sno).first()
    return render_template('update.html', todo=todo)

if __name__ == '__main__':
    app.run(debug=True)
