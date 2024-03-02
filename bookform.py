from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, FileField, TextAreaField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed

class bookForm(FlaskForm):
    judul = StringField(label='Judul', validators=[DataRequired()])
    penulis = StringField(label='Penulis', validators=[DataRequired()])
    halaman = IntegerField(label="Halaman", validators=[DataRequired()])
    genre = SelectField(label="Genre", choices=["Fiksi","Non-Fiksi","Buku Pengetahuan"])
    deskripsi = TextAreaField(label="Deskripsi", validators=[DataRequired()])
    file = FileField(label="Upload File (.PDF)", validators=[FileAllowed(['pdf'])])
    submit = SubmitField(label="Kirim")