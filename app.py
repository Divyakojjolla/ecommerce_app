from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# ---------------- MODELS ---------------- #

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    user_id = db.Column(db.Integer)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200))
    post_id = db.Column(db.Integer)


# ---------------- LOGIN ---------------- #

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------- ROUTES ---------------- #

@app.route('/')
def home():
    posts = Post.query.all()
    return render_template('dashboard.html', posts=posts)


# REGISTER
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        existing_user = User.query.filter_by(username=request.form['username']).first()
        if existing_user:
            return "Username already exists!"

        user = User(username=request.form['username'], password=request.form['password'])
        db.session.add(user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')


# LOGIN
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if user:
            login_user(user)
            return redirect('/')
        return "Invalid credentials"

    return render_template('login.html')


# LOGOUT
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


# CREATE POST
@app.route('/create', methods=['GET','POST'])
@login_required
def create_post():
    if request.method == 'POST':
        post = Post(
            title=request.form['title'],
            content=request.form['content'],
            user_id=current_user.id
        )
        db.session.add(post)
        db.session.commit()
        return redirect('/')

    return render_template('create_post.html')


# VIEW POST + COMMENTS
@app.route('/post/<int:post_id>', methods=['GET','POST'])
@login_required
def view_post(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        comment = Comment(
            text=request.form['comment'],
            post_id=post.id
        )
        db.session.add(comment)
        db.session.commit()

    comments = Comment.query.filter_by(post_id=post.id).all()

    return render_template('post.html', post=post, comments=comments)


# ---------------- RUN ---------------- #

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)