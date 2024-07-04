from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user,current_user
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey1807'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tips.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique = True, nullable = False)
    password = db.Column(db.String(100), nullable = False)

class Tip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable = False)
    amount = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# with app.app_context():
    # db.create_all()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    tips = Tip.query.filter_by(user_id=current_user.id).all()
    total_tips = sum(tip.amount for tip in tips)

    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())

    tips_by_day = {i: 0 for i in range(7)}

    for tip in tips:
        if start_of_week <= tip.date <= start_of_week + timedelta(days=6):
            weekday = tip.date.weekday()
            tips_by_day[weekday] += tip.amount

    tips_by_day_lst = [tips_by_day[i] for i in range(7)]

    print("tips_by_day_lst:", tips_by_day_lst)  # Debug statement

    return render_template('index.html', tips=tips, total_tips = total_tips, tips_by_day_json=json.dumps(tips_by_day_lst))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_tip():
    if request.method == 'POST':
        date_str = request.form.get('date')
        amount = request.form.get('amount')
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            amount = float(amount)
        except ValueError:
            return redirect(url_for('add_tip'))
        
        new_tip = Tip(date=date, amount=float(amount), user_id=current_user.id)
        db.session.add(new_tip)
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('add_tip.html')

@app.route('/remove', methods=['GET','POST'])
@login_required
def remove_tip():
    tip_id = request.form.get('tip_id')
    tip = Tip.query.filter_by(id=tip_id, user_id=current_user.id).first()
    if tip:
        db.session.delete(tip)
        db.session.commit()
        flash('Tip removed successfully','success')
    else:
        flash('Tip not found')
    current_date = datetime.now().strftime('%Y-%m-%d')
    return redirect(url_for('index'))

@app.route("/admin")
def view():
    return render_template('admin.html', values=User.query.all())


if __name__ == '__main__':
    app.run(debug=True, port=5001)