from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from flask_sqlalchemy import SQLAlchemy

app=Flask(__name__)
app.config["SECRET_KEY"]='alphagamma'
app.config["SQLALCHEMY_DATABASE_URI"]='sqlite:///app.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db=SQLAlchemy(app)



class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Full_name = db.Column(db.String, nullable=False)
    User_password = db.Column(db.String, nullable=False)
    Email = db.Column(db.String, unique=True, nullable=False)
    Mobile = db.Column(db.String(10), unique=True, nullable=False)
    Gender = db.Column(db.String(6))
    Role = db.Column(db.String, default="User")

    def set_password(self, password):
        self.User_password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.User_password, password)


class ParkingLot(db.Model):
    __tablename__ = 'parking_lot'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parking_location_name = db.Column(db.String(30), nullable=False)
    price_per_hour = db.Column(db.Integer, nullable=False)
    Address = db.Column(db.String, nullable=False)
    Pincode = db.Column(db.String(6), nullable=False)
    Maximum_number_of_spot = db.Column(db.Integer, nullable=False)
    
    spots = db.relationship('ParkingSpot', backref='lot', cascade="all, delete-orphan")


class ParkingSpot(db.Model):
    __tablename__ = 'parking_spot'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    spot_number = db.Column(db.String(5), nullable=False)
    status = db.Column(db.String(1), default="A")
    reservations = db.relationship('Reservation', backref='spot', cascade="all, delete-orphan")


class Reservation(db.Model):
    __tablename__ = 'reservation'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime)
    amount_paid = db.Column(db.Float)
    vehicle_number = db.Column(db.String, nullable=False)

def create_admin():
    with app.app_context():
        if not User.query.filter_by(Role='Admin').first():
            admin = User(Full_name="Admin1", Email='admin99@gmail.com',Mobile='9919991900', Role='Admin', Gender="Male")
            admin.set_password('admin99')
            db.session.add(admin)
            db.session.commit()

@app.route("/")
def home():
    return redirect(url_for('login'))

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username=request.form['username']
        password=request.form['password']

        user = User.query.filter_by(Email=username).first()
        flash("Login Succesfully", "success")

        if user and user.check_password(password):
            session['user_id']=user.id
            session['username']= user.Email
            session["role"]= user.Role

            if user.Role=="Admin":
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for("user_dashboard"))
        flash("Invalid Email or Password", "danger")
    return render_template('login.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method=="POST":
        username= request.form["username"]
        email= request.form['email']
        password=request.form['password']
        mobile= request.form['mobile']
        gender=request.form['gender']

        if User.query.filter_by(Email= email).first():
            flash("Email already exists",' danger')
            return redirect(url_for('register'))
        if User.query.filter_by(Mobile=mobile).first():
            flash("Mobile already registered",' danger')
            return redirect(url_for('register'))
        new_user= User(Full_name=username, Email=email, Mobile=mobile, Gender=gender)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successfull!!!, Please login", "success")
        return redirect(url_for('login'))
    return render_template('register.html')












with app.app_context():
    db.create_all()
    create_admin()

if __name__== '__main__':
    app.run(debug=True)