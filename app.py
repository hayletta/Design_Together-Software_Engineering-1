from flask import Flask, render_template, url_for, redirect, flash, request
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, DateField
from wtforms.validators import DataRequired, EqualTo
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from PIL import Image
import requests
import secrets
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = 'password'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Class for user data
class User(UserMixin):
    def __init__(self, id, email, birthday, username, bio='', profile_pic='default.jpg', posts=None):
        self.id = id
        self.username = username
        self.email = email
        self.birthday = birthday
        self.bio = bio
        self.profile_pic = profile_pic
        self.posts = posts if posts else []


users = {'username': {'password': 'password'}}


# Function to load a user
@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)


# Class for the login form on the login page
class LoginForm(FlaskForm):
    username = StringField('Enter Username', validators=[DataRequired()])
    password = PasswordField('Enter Password', validators=[DataRequired()])
    submit = SubmitField('Click Here to Log In (Account Required)')
    help = SubmitField('Need Help? Contact Customer Support!')


# login page route this uses the microservice my partner created for authenticate so users be authenticated.
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        api_url = "http://auth361.vercel.app/auth"
        data = {"username": username, "password": password}
        response = requests.post(api_url, json=data)
        if response.status_code == 200:
            user = User(id=username, email="", birthday="", username=username)
            users[username] = user
            login_user(user)
            flash('Welcome Back', 'success')
            return redirect(url_for('account_home'))
        else:
            flash('Wrong username or password. If you want to create an account click the create account button')

    return render_template('login.html', form=form)


# class for the register form on the create_account page
class RegisterForm(FlaskForm):
    username = StringField('Enter Username', validators=[DataRequired()])
    password = PasswordField('Enter Password', validators=[DataRequired()])
    password_confirm = PasswordField('Re-enter Password', validators=[DataRequired(),
                                                                      EqualTo('password', message='Match Passwords')])
    email = StringField('Enter Email Address', validators=[DataRequired()])
    birthday = DateField('Enter Birthdate', format='%Y-%m-%d', validators=[DataRequired()])
    create_account = SubmitField('Join the party!')


# Route for the create_account page this also uses the microservice my partner implemented so users can have their
# accounts created and stored.
@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        password_confirmation = form.password_confirm.data
        email = form.email.data
        birthday = form.birthday.data
        api_url = "http://auth361.vercel.app/create"
        data = {"username": username, "password": password}
        response = requests.post(api_url, json=data)
        if response.status_code == 201:
            flash('Account created, welcome to BuildTogether! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash("username already exists, choose another", 'danger')
    return render_template('create_account.html', form=form)


# This is the route for a users home page.
@app.route('/account_home', methods=['GET', 'POST'])
@login_required
def account_home():
    editing_bio = request.args.get('editing_bio') == 'True'
    editing_profile_pic = request.args.get('editing_profile_pic') == 'True'

    form = AccountInfo()
    if form.validate_on_submit():
        if form.profile_pic.data:
            pic_file = save_picture(form.profile_pic.data)
            current_user.profile_pic = pic_file
        current_user.bio = form.bio.data
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account_home'))
    elif request.method == 'GET':
        form.bio.data = current_user.bio

    if current_user.profile_pic:
        profile_pic = url_for('static', filename='profile_pics/' + current_user.profile_pic)
    else:
        profile_pic = url_for('static', filename='profile_pics/default.jpg')

    image_post_form = Images()
    return render_template('account_home.html', profile_pic=profile_pic, form=form,
                           image_post_form=image_post_form, posts=current_user.posts,
                           editing_bio=editing_bio, editing_profile_pic=editing_profile_pic)


# Stores the bio and profile pic.
class AccountInfo(FlaskForm):
    bio = StringField('Bio', validators=[DataRequired()])
    profile_pic = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')


# Gives the profile page the ability to save pictures.
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    if not os.path.exists(os.path.dirname(picture_path)):
        os.makedirs(os.path.dirname(picture_path))

    output_size = (1000, 1000)
    image = Image.open(form_picture)
    if image.width > 1000:
        output_size = (1000, int((image.height / image.width) * 1000))
        image.thumbnail(output_size)

    image.save(picture_path)
    return picture_fn


# Class for the images to be posted
class Images(FlaskForm):
    picture = FileField('Post a Project!', validators=[FileAllowed(['jpg', 'png'])])
    caption = StringField('Caption')
    submit = SubmitField('Post')


image_posts = {}


# Route for when an image is posted.
@app.route('/post_image', methods=['GET', 'POST'])
@login_required
def post_image():
    form = Images()
    if form.validate_on_submit():
        if form.picture.data:
            pic_file = save_picture(form.picture.data)
            caption = form.caption.data
            post_id = len(current_user.posts)
            new_post = {'id': post_id, 'picture': pic_file, 'caption': caption}
            current_user.posts.append(new_post)
            return redirect(url_for('account_home'))
    return render_template('post_image.html', title='Post Image', form=form)


# route for when a post is deleted
@app.route('/delete_post/<post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post_id = int(post_id)
    current_user.posts = [post for post in current_user.posts if post['id'] != post_id]
    return redirect(url_for('account_home'))


# Route for search
@app.route('/search', methods=['GET'])
@login_required
def search():
    form = AccountInfo()
    image_post_form = Images()
    query = request.args.get('query')
    search_results = []
    for username, user in users.items():
        if query.lower() in username.lower():
            search_results.append(user)

    if current_user.profile_pic:
        profile_pic = url_for('static', filename='profile_pics/' + current_user.profile_pic)
    else:
        profile_pic = url_for('static', filename='profile_pics/default.jpg')

    return render_template('search_results.html', profile_pic=profile_pic, form=form,
                           image_post_form=image_post_form, posts=current_user.posts,
                           search_results=search_results)


# route for viewing another profile
@app.route('/view_profile/<username>')
@login_required
def view_profile(username):
    user = users.get(username)
    if user:
        return render_template('profile.html', user=user)
    else:
        flash('User not found!', 'danger')
        return redirect(url_for('account_home'))


# Route for logging out
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    flash('Successfully logged out', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)









