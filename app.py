from flask import Flask, render_template, url_for, redirect, flash, get_flashed_messages
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField
from wtforms.validators import DataRequired, EqualTo
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

app = Flask(__name__)
app.config['SECRET_KEY'] = 'password'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, email, birthday):
        self.id = id
        self.email = email
        self.birthday = birthday


users = {'username': {'password': 'password'}}


def authenticate(username, password):
    if username in users:
        if username in users and users[username]['password'] == password:
            return User(username, users[username]['email'], users[username]['birthday'])
        else:
            return None, "wrong_password"
    return None, "wrong_username"


@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id, users[user_id]['email'], users[user_id]['birthday'])
    return None

class LoginForm(FlaskForm):
    username = StringField('Enter Username', validators=[DataRequired()])
    password = PasswordField('Enter Password', validators=[DataRequired()])
    submit = SubmitField('Click Here to Log In (Account Required)')
    help = SubmitField('Need Help? Contact Customer Support!')


class RegisterForm(FlaskForm):
    username = StringField('Enter Username', validators=[DataRequired()])
    password = PasswordField('Enter Password', validators=[DataRequired()])
    password_confirm = PasswordField('Re-enter Password', validators=[DataRequired(),
                                                                      EqualTo('password', message='Match Passwords')])
    email = StringField('Enter Email Address', validators=[DataRequired()])
    birthday = DateField('Enter Birthdate', format='%Y-%m-%d', validators=[DataRequired()])
    create_account = SubmitField('Join the party!')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user, status = authenticate(form.username.data, form.password.data)
        if user:
            login_user(user)
            flash('Welcome Back', 'success')
            return redirect(url_for('protected'))
        elif status == "wrong_password":
                flash("Incorrect password, try again", "danger")
        else:
            flash('Wrong username if you want to create an account click the create account button!',
                  'danger')
    return render_template('login.html', form=form)


@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        password_confirmation = form.password_confirm.data
        email = form.email.data
        birthday = form.birthday.data
        if username not in users:
            users[username] = {'password': password, 'email': email, 'birthday': birthday}
            flash('Account created, welcome to BuildTogether! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash("username already exists, choose another", 'danger')
    return render_template('create_account.html', form=form)


@app.route('/protected')
@login_required
def protected():
    return 'You are logged in!'


@app.route('/logout')
def logout():
    logout_user()
    flash('Successfully logged out', 'success')
    return  redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)





