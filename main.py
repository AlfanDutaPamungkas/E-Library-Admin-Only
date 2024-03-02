from flask import Flask, render_template, redirect, url_for, request, send_file, flash, abort
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_bootstrap import Bootstrap5
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from loginform import LoginForm
from bookform import bookForm
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from random_id import generate_random_string
from dotenv import load_dotenv
import io
import os


load_dotenv()

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if (current_user.is_authenticated and current_user.role != "admin") or not current_user.is_authenticated:
            return abort(403)
        return f(*args, **kwargs)        
    return decorated_function

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD")
app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY")
Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URL")
db = SQLAlchemy()
db.init_app(app)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(20))
    role = db.Column(db.String(10), nullable=False, default='user')

class Book(db.Model):
    id = db.Column(db.String(8), primary_key=True)
    judul = db.Column(db.String(250), nullable=False)
    penulis = db.Column(db.String(250), nullable=False)
    halaman = db.Column(db.Integer, nullable=False)
    genre = db.Column(db.String(250), nullable=False)
    deskripsi = db.Column(db.String(500), nullable=False)
    filename = db.Column(db.String(255))
    file_data = db.Column(db.LargeBinary)

@app.before_request
def setup():
    with app.app_context():
        db.create_all()
        create_admin()
        
def create_admin():
    admin = User.query.filter_by(email=ADMIN_EMAIL).first()
    if not admin:
        hash_and_salted_password = generate_password_hash(
            ADMIN_PASS,
            method='pbkdf2:sha256',
            salt_length=8
        )
        admin = User(email=ADMIN_EMAIL, password=hash_and_salted_password, role='admin')
        db.session.add(admin)
        db.session.commit()

@app.route("/",methods=["GET","POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        
        result = db.session.execute(db.select(User).where(User.email == email))
        user = result.scalar()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin'))
        else:
            flash("The email or password is incorrect, please try again")
            return redirect(url_for('login'))
        
    return render_template('login.html',form=login_form)

@app.route("/admin")
@admin_only
def admin():
    order = request.args.get("order")
    all_books = db.session.execute(db.select(Book).order_by(Book.judul)).scalars()
    if order == "asc": 
        return render_template("admin.html", books=all_books)
    else:
        desc_all_books = db.session.execute(db.select(Book).order_by(desc(Book.judul))).scalars()
        return render_template("admin.html", books=desc_all_books)

@app.route("/add", methods=["GET","POST"])
@admin_only
def add():
    book_form = bookForm()
    if  book_form.validate_on_submit():
        new_book = Book(
            id = generate_random_string(),
            judul = book_form.judul.data,
            penulis = book_form.penulis.data,
            halaman = book_form.halaman.data,
            genre = book_form.genre.data,
            deskripsi = book_form.deskripsi.data,
            filename=book_form.file.data.filename,  
            file_data=book_form.file.data.read()
        )
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template("form.html",form = book_form, is_edit = False)

@app.route("/edit/<string:id>", methods=["GET","POST"])
@admin_only
def edit(id):
    book_to_update = db.get_or_404(Book, id)
    book_form = bookForm(
        judul = book_to_update.judul,
        penulis = book_to_update.penulis,
        halaman = book_to_update.halaman,
        genre = book_to_update.genre,
        deskripsi = book_to_update.deskripsi,
        file = book_to_update.filename
    )
    
    if  book_form.validate_on_submit():
        book_to_update.judul = book_form.judul.data
        book_to_update.penulis = book_form.penulis.data
        book_to_update.halaman = book_form.halaman.data
        book_to_update.genre = book_form.genre.data
        book_to_update.deskripsi = book_form.deskripsi.data
        book_to_update.filename = book_form.file.data.filename
        book_to_update.file_data = book_form.file.data.read()

        db.session.commit()
        return redirect(url_for('admin'))
    return render_template("form.html", form=book_form, is_edit=True)

@app.route("/delete/<string:id>")
@admin_only
def delete(id):
    book_to_delete = db.get_or_404(Book, id)
    db.session.delete(book_to_delete)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route("/search", methods=["POST"])
@admin_only
def search():
    all_books = db.session.execute(db.select(Book).order_by(Book.judul)).scalars()
    book_name = request.form["search"].lower()
    return render_template("search.html", search_name=book_name, books=all_books) 
    
@app.route("/download")
@admin_only
def download():
    book_id = request.args.get("id")
    book = db.session.get(Book, book_id)
    if book:
        return send_file(
            io.BytesIO(book.file_data),
            as_attachment=True,
            download_name=f"{book.filename}",
            mimetype="application/pdf"
        )
    else:
        return "Buku tidak ditemukan", 404
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)