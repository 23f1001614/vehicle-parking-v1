from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from functools import wraps
import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = 'alphagamma'
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///app.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Full_name = db.Column(db.String, nullable=False)
    User_password = db.Column(db.String, nullable=False)
    Email = db.Column(db.String, unique=True, nullable=False)
    Mobile = db.Column(db.String(10), unique=True, nullable=False)
    Gender = db.Column(db.String(6))
    Role = db.Column(db.String, default="User")
    Reservations = db.relationship('Reservation', backref='user', lazy=True)

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


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.Role != "Admin":
            flash("Admin access required", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function



def create_admin():
    with app.app_context():
        if not User.query.filter_by(Role='Admin').first():
            admin = User(Full_name="Admin1", Email='admin99@gmail.com', Mobile='9919991900', Role='Admin', Gender="Male")
            admin.set_password('admin99')
            db.session.add(admin)
            db.session.commit()



@app.route("/")
def home():
    if current_user.is_authenticated:
        if current_user.Role == "Admin":
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for("user_dashboard"))
    return redirect(url_for('login'))


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(Email=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Login successful", "success")
            return redirect(url_for('admin_dashboard' if user.Role == "Admin" else 'user_dashboard'))

        flash("Invalid Email or Password", "danger")
    return render_template('login.html')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form['email']
        password = request.form['password']
        mobile = request.form['mobile']
        gender = request.form['gender']

        if User.query.filter_by(Email=email).first():
            flash("Email already exists", 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(Mobile=mobile).first():
            flash("Mobile already registered", 'danger')
            return redirect(url_for('register'))

        new_user = User(Full_name=username, Email=email, Mobile=mobile, Gender=gender)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    lots = ParkingLot.query.all()
    available_spots = ParkingSpot.query.filter_by(status='A').count()
    occupied_spots = ParkingSpot.query.filter_by(status='O').count()
    users_count = User.query.filter_by(Role="User").count()
    return render_template("admin/admin_dashboard.html", lots=lots,
                           available_spots=available_spots,
                           occupied_spots=occupied_spots,
                           users_count=users_count)


@app.route("/admin/create_lot", methods=['GET', 'POST'])
@login_required
@admin_required
def create_lot():
    if request.method == "POST":
        name = request.form['name']
        address = request.form["address"]
        pincode = request.form["pincode"]
        price = int(request.form["price"])
        num_of_spots = int(request.form["spots"])

        new_lot = ParkingLot(parking_location_name=name,
                             price_per_hour=price,
                             Address=address,
                             Pincode=pincode,
                             Maximum_number_of_spot=num_of_spots)
        db.session.add(new_lot)
        db.session.commit()

        for i in range(1, num_of_spots + 1):
            spot = ParkingSpot(Lot_id=new_lot.id,
                               spot_number=f"P-{i}",
                               status="A")
            db.session.add(spot)
        db.session.commit()
        flash("Parking lot created successfully!", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template("admin/create_lot.html")


@app.route("/admin/manage_lots", methods=['GET', 'POST'])
@login_required
@admin_required
def manage_lots():
    lots = ParkingLot.query.all()
    return render_template("admin/manage_lots.html", lots=lots)


@app.route("/admin/view_lot/<int:lot_id>", methods=["GET", "POST"])
@login_required
@admin_required
def view_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    spots_ = ParkingSpot.query.filter_by(Lot_id=lot_id).all()
    return render_template("admin/view_lot.html", lot=lot, spots=spots_)


@app.route("/admin/delete_lot/<int:lot_id>", methods=["GET", "POST"])
@login_required
@admin_required
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    occupied_spots = ParkingSpot.query.filter_by(Lot_id=lot_id, status="O").count()
    if occupied_spots > 0:
        flash("Cannot delete lot with occupied spots.", "danger")
        return redirect(url_for("manage_lots"))
    ParkingSpot.query.filter_by(Lot_id=lot_id).delete()
    db.session.delete(lot)
    db.session.commit()
    flash("Parking lot deleted successfully!", "success")
    return redirect(url_for("manage_lots"))


@app.route("/admin/view_user")
@login_required
@admin_required
def view_users():
    users = User.query.filter_by(Role="User").all()
    return render_template("admin/view_user.html", users=users)

@app.route('/admin/user/<int:user_id>/reservations')
@login_required
@admin_required
def admin_user_reservations(user_id):
    user = User.query.get_or_404(user_id)

    all_reservations = Reservation.query.filter_by(user_id=user.id).order_by(Reservation.check_in.desc()).all()

    return render_template('admin/admin_user_reservation.html', user=user, reservations=all_reservations)


@app.route("/admin/edit_lot/<int:lot_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    current_total = lot.Maximum_number_of_spot
    all_spots = ParkingSpot.query.filter_by(Lot_id=lot.id).all()

    if request.method == 'POST':
        lot.parking_location_name = request.form['name']
        lot.Address = request.form['address']
        lot.Pincode = request.form['pincode']
        lot.price_per_hour = int(request.form['price'])

        new_total = int(request.form['total_spots'])

        if new_total > current_total:
            for i in range(current_total + 1, new_total + 1):
                spot = ParkingSpot(
                    Lot_id=lot.id,
                    spot_number=f"P-{i}",
                    status='A'
                )
                db.session.add(spot)
            lot.Maximum_number_of_spot = new_total
            flash(f'Added {new_total - current_total} new parking spots!', 'success')

        elif new_total < current_total:
            spots_to_remove = [
                spot for spot in all_spots
                if int(spot.spot_number.split('-')[-1]) > new_total
            ]
            occupied = [s for s in spots_to_remove if s.status == 'O']

            if occupied:
                flash(f"Cannot reduce spots. {len(occupied)} of the to-be-removed spots are occupied!", 'danger')
                return redirect(url_for('edit_lot', lot_id=lot.id))

            for s in spots_to_remove:
                db.session.delete(s)

            lot.Maximum_number_of_spot = new_total
            flash(f'Removed {current_total - new_total} parking spots.', 'success')

        db.session.commit()
        flash('Parking lot updated successfully!', 'success')
        return redirect(url_for('view_lot', lot_id=lot.id))

    return render_template("admin/edit_lot.html", lot=lot, current_spots=current_total)


@app.route('/user/dashboard')
@login_required
def user_dashboard():
    active_reservation = Reservation.query.filter_by(user_id=current_user.id ,check_out=None).all() 
    past_reservation = Reservation.query.filter(
        Reservation.user_id == current_user.id,
        Reservation.check_out != None
    ).order_by(Reservation.check_in.desc()).limit(5).all()

    return render_template('users/user_dashboard.html',
                           active_reservation=active_reservation,
                           past_reservation=past_reservation)


@app.route('/user/find_parking', methods=["GET", "POST"])
@login_required
def find_parking():
    if request.method == "POST":
        pincode= request.form["pincode"]
        vehicle_number= request.form["vehicle_number"]
        if pincode:
            lots= ParkingLot.query.filter_by(Pincode=pincode)
        else:
            lots= ParkingLot.query.all()
        available_lots=[]
        for lot in lots:
            available_spots=ParkingSpot.query.filter_by(Lot_id=lot.id, status="A").count()
            if available_spots>0:
                available_lots.append({
                    "lot": lot,
                    'available_spots': available_spots
                })
        return render_template("users/find_parking.html", lots=available_lots, vehicle_number=vehicle_number)
    return render_template("users/find_parking.html")

@app.route('/user/reserve_spot/<int:lot_id>', methods=["GET", "POST"])
@login_required
def reserve_spot(lot_id):
    vehicle_number= request.form["vehicle_number"]
    spot=ParkingSpot.query.filter_by(Lot_id=lot_id, status="A").first()
    if not spot:
        flash("No available spots in this lot", "danger")
        return redirect(url_for("find_parking"))
    lot = ParkingLot.query.get(lot_id)
    reservation= Reservation(spot_id=spot.id, user_id=current_user.id,
                             check_in=datetime.datetime.now(),
                             vehicle_number=vehicle_number)
    spot.status="O"
    db.session.add(reservation)
    db.session.commit()
    flash(f'Spot {spot.spot_number} reserved successfully at {lot.parking_location_name}.',"success")
    return redirect(url_for("user_dashboard"))


@app.route('/user/release_spot/<int:reservation_id>', methods=["GET", "POST"])
@login_required
def release_spot(reservation_id):
    reservation=Reservation.query.get_or_404(reservation_id)
    lot=reservation.spot.lot
    time_parked=datetime.datetime.now()-reservation.check_in
    hours_parked= max(1, time_parked.total_seconds()/3600)
    amount=round(hours_parked* lot.price_per_hour,2)
    reservation.check_out=datetime.datetime.now()
    reservation.amount_paid=amount
    reservation.spot.status="A"
    db.session.commit()
    return redirect(url_for("user_dashboard"))
@app.route('/user/bookings')
@login_required
def my_reservation():
    active_reservation = Reservation.query.filter_by(user_id=current_user.id ,check_out=None).all() 
    past_reservation = Reservation.query.filter(
        Reservation.user_id == current_user.id,
        Reservation.check_out != None).all()
    for res in past_reservation:
        duration = res.check_out - res.check_in
        res.duration_minutes = int(duration.total_seconds() // 60)
        res.duration_hours = round(duration.total_seconds() / 3600, 2)

    return render_template('users/my_reservation.html',
                           active_reservation=active_reservation,
                           past_reservation=past_reservation)













with app.app_context():
    db.create_all()
    create_admin()

if __name__== '__main__':
    app.run(debug=True)