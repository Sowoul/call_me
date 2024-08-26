from flask import Flask, render_template, redirect, url_for, request, session
from flask_socketio import SocketIO, join_room, emit
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SECRET_KEY"] = "IDK123"

socket = SocketIO(app=app)
db = SQLAlchemy(app)

class User(db.Model):
    user = db.Column("name", db.String(16), primary_key=True)
    passwd = db.Column("passwd", db.String(164))

    def __init__(self, name, passwd):
        self.user = name
        self.passwd = passwd

@app.route('/')
def red():
    name = session.get("name", "")
    if db.session.query(User).filter_by(user=name).first() is None:
        return redirect(url_for('login'))
    return redirect(url_for('welcome'))

@app.route('/login', methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name", "")
        password = request.form.get("password", "")
        existing = db.session.query(User).filter_by(user=name).first()
        if not existing or not check_password_hash(existing.passwd, password):
            return redirect(url_for('login'))
        session["name"] = name
        return redirect(url_for('welcome'))
    return render_template('login.html')

@app.route('/signup', methods=["GET", "POST"])
def signup():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name", "")
        password = request.form.get("password", "")
        existing = db.session.query(User).filter_by(user=name).first()
        if existing:
            return redirect(url_for('signup'))
        password_hash = generate_password_hash(password)
        newuser = User(name, password_hash)
        db.session.add(newuser)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/call')
def welcome():
    return render_template("wait.html")

@socket.on('connect')
def connected():
    name = session.get("name", '')
    join_room(name)
    print(f"Connected {name}")

@socket.on('call')
def handle_call(data):
    name = session.get('name', "")
    target = data["target"]

    # Emit the offer to the target user
    emit('offer', {'offer': data['offer'], 'source': name}, to=target)

@socket.on('answer')
def handle_answer(data):
    target = data["target"]
    
    # Emit the answer back to the caller
    emit('answer', {'answer': data['answer']}, to=target)

@socket.on('call_rejected')
def handle_rejection(data):
    source = data["source"]
    # Notify the caller that the call was rejected
    emit('call_rejected', to=source)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socket.run(app=app, port=8000, debug=True)
