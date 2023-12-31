import os
from dotenv import load_dotenv
from functools import wraps
from datetime import date
from hashlib import md5
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import login_user, LoginManager, login_required, current_user, logout_user
from sqlalchemy import inspect
from werkzeug.security import generate_password_hash, check_password_hash
from database import db_session, engine, init_db
from models import User, BlogPost, Comment
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm


load_dotenv()
app = Flask(__name__)
Bootstrap(app)
ckeditor = CKEditor(app)
app.secret_key = os.getenv('APP_KEY')

if not inspect(engine).has_table("blog_post_table"):
    init_db()

login_manager = LoginManager()
login_manager.init_app(app)


def gravatar_url(email, size=100, rating='g', default='retro', force_default=False):
    hash_value = md5(email.lower().encode('utf-8')).hexdigest()
    return f"https://www.gravatar.com/avatar/{hash_value}?s={size}&d={default}&r={rating}&f={force_default}"


app.jinja_env.globals.update(gravatar_url=gravatar_url)


@login_manager.user_loader
def load_user(user_id):
    return db_session.get(User, int(user_id))


# test for decorators
def admin_only(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return func(*args, **kwargs)
    return decorated_function


# Render home page using DB
@app.route("/")
def home():

    posts_data = db_session.query(BlogPost).all()
    return render_template("index.html", data=posts_data)


# Create new post
@app.route('/new-post', methods=['POST', 'GET'])
@login_required
def create_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=date.today().strftime("%B %d, %Y"),
            body=form.body.data,
            author=current_user,
            img_url=form.img_url.data
        )
        db_session.add(new_post)
        db_session.commit()
        return redirect(url_for('home'))
    return render_template('make-post.html', form=form)


# Edit post
@app.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post_to_edit = db_session.get(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post_to_edit.title,
        subtitle=post_to_edit.subtitle,
        img_url=post_to_edit.img_url,
        body=post_to_edit.body
    )
    if edit_form.validate_on_submit():
        post_to_edit.title = edit_form.title.data
        post_to_edit.subtitle = edit_form.subtitle.data
        post_to_edit.img_url = edit_form.img_url.data
        post_to_edit.body = edit_form.body.data
        db_session.commit()
        return redirect(url_for('post', post_id=post_id))
    return render_template('make-post.html', form=edit_form, is_edit=True)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/post/<int:post_id>", methods=["POST", "GET"])
def post(post_id):
    post_data = db_session.get(BlogPost, post_id)
    form = CommentForm()

    if current_user.is_authenticated and form.validate_on_submit():
        new_comment = Comment(
            author=current_user,
            post=post_data,
            text=form.body.data
        )
        db_session.add(new_comment)
        db_session.commit()
        return redirect(url_for('post', post_id=post_id))
    return render_template("post.html", post_data=post_data, form=form)


# Delete post from DB
@app.route('/delete/<int:post_id>')
@login_required
def delete_post(post_id):
    post_to_delete = db_session.get(BlogPost, post_id)
    db_session.delete(post_to_delete)
    db_session.commit()
    return redirect(url_for('home'))


@app.route("/contact", methods=['POST', 'GET'])
def contact():
    if request.method == 'POST':
        json_data = dict(request.form)
        print(json_data)
        return render_template("contact.html", msg_sent=True)
    return render_template("contact.html", msg_sent=False)


@app.route("/register", methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        if db_session.query(User).filter_by(email=email).first():
            flash("This email already signed up.")
            return redirect(url_for('login'))
        hash_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            name=form.name.data,
            email=email,
            password=hash_password,
        )
        db_session.add(new_user)
        db_session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template('register.html', form=form)


@app.route("/login", methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = db_session.query(User).filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("Wrong email or password. Try again.")
            return redirect(url_for('login'))
    return render_template("login.html", form=form)


@app.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == "__main__":
    app.run(debug=True)

