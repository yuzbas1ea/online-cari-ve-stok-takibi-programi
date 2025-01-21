from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SubmitField, PasswordField, DateField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from wtforms.widgets import DateTimeInput
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://db_user:EEGnGEuQQy0OmJ1wFn09BtdDQjfgEBO5@dpg-cu80hu9opnds73ej1mt0-a/borc_stok_db'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Debtor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    product = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    debts = db.relationship('Debt', backref='debtor', lazy=True)

class Debt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    debtor_id = db.Column(db.Integer, db.ForeignKey('debtor.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    payments = db.relationship('Payment', backref='debt', lazy=True)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    debt_id = db.Column(db.Integer, db.ForeignKey('debt.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

class LoginForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Şifre', validators=[DataRequired()])
    submit = SubmitField('Giriş Yap')

class RegisterForm(FlaskForm):
    username = StringField('Kullanıcı Adı', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    password = PasswordField('Şifre', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Şifreyi Onayla', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Kayıt Ol')

class AddDebtorForm(FlaskForm):
    name = StringField('Borçlu İsmi', validators=[DataRequired()])
    product = StringField('Ürün İsmi', validators=[DataRequired()])
    price = FloatField('Ürün Fiyatı', validators=[DataRequired()])
    address = StringField('Adres')
    phone = StringField('Telefon Numarası')
    submit = SubmitField('Ekle')

class AddDebtForm(FlaskForm):
    product_name = StringField('Ürün Adı', validators=[DataRequired()])
    amount = FloatField('Borç Miktarı', validators=[DataRequired()])
    date = DateField('Borç Tarihi', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Borç Ekle')

class AddPaymentForm(FlaskForm):
    debt_id = IntegerField('Borç ID', validators=[DataRequired()])
    amount = FloatField('Tahsilat Miktarı', validators=[DataRequired()])
    date = DateTimeField('Tahsilat Tarihi', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Tahsilat Ekle')

class StockForm(FlaskForm):
    product = StringField('Ürün İsmi', validators=[DataRequired()])
    quantity = IntegerField('Stok Miktarı', validators=[DataRequired()])
    price = FloatField('Fiyat', validators=[DataRequired()])
    submit = SubmitField('Ekle')

class UpdateStockForm(FlaskForm):
    quantity = IntegerField('Stok Miktarı', validators=[DataRequired()])
    price = FloatField('Fiyat', validators=[DataRequired()])
    submit = SubmitField('Güncelle')

class DebtForm(FlaskForm):
    amount = FloatField('Miktar', validators=[DataRequired()])
    date = DateField('Tarih', validators=[DataRequired()], default=datetime.date.today)
    submit = SubmitField('Borç Ekle')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    return redirect(url_for('index'))

@app.route('/')
def root():
    return redirect(url_for('index'))

@app.route('/index')
def index():
    borclar = Debtor.query.all()
    stocks = Stock.query.all()
    return render_template('index.html', borclar=borclar, stocks=stocks, current_user=None)

@app.route('/cari_takip', methods=['GET', 'POST'])
def cari_takip():
    debtors = Debtor.query.all()
    form = AddDebtorForm()
    debtor_debts = {}
    for debtor in debtors:
        debts = Debt.query.filter_by(debtor_id=debtor.id).all()
        payments = Payment.query.filter(Payment.debt_id.in_([debt.id for debt in debts])).all()
        total_debt = sum(debt.amount for debt in debts)
        total_payment = sum(payment.amount for payment in payments)
        current_debt = total_debt - total_payment
        debtor_debts[debtor.id] = current_debt

    if form.validate_on_submit():
        try:
            debtor = Debtor(name=form.name.data, product=form.product.data, 
                            price=form.price.data, address=form.address.data, 
                            phone=form.phone.data)
            db.session.add(debtor)
            db.session.commit()
            flash('Yeni borçlu başarıyla eklendi.', 'success')
            return redirect(url_for('cari_takip'))
        except Exception as e:
            db.session.rollback()
            flash(f'Borçlu eklenirken bir hata oluştu: {str(e)}', 'error')
    return render_template('cari_takip.html', debtors=debtors, debtor_debts=debtor_debts, form=form)

@app.route('/debtors/<int:debtor_id>', methods=['GET', 'POST'])
def debtor_detail(debtor_id):
    debtor = Debtor.query.get_or_404(debtor_id)
    debt_form = AddDebtForm()
    payment_form = AddPaymentForm()

    if request.method == 'POST':
        if 'debt_submit' in request.form:
            if debt_form.validate_on_submit():
                try:
                    debt = Debt(
                        user_id=1,  # Anonim kullanıcı olarak sabit bir ID kullanımı
                        debtor_id=debtor_id,
                        product_name=debt_form.product_name.data,
                        amount=debt_form.amount.data,
                        due_date=debt_form.date.data
                    )
                    db.session.add(debt)
                    db.session.commit()
                    flash('Borç eklendi.', 'success')
                    return redirect(url_for('debtor_detail', debtor_id=debtor_id))
                except Exception as e:
                    db.session.rollback()
                    flash(f'Borç eklenirken bir hata oluştu: {str(e)}', 'error')
            else:
                flash('Form doğrulanamadı. Lütfen tüm alanları doğru doldurduğunuzdan emin olun.', 'error')

        elif 'payment_submit' in request.form:
            if payment_form.validate_on_submit():
                try:
                    debt_id = payment_form.debt_id.data
                    debt = db.session.get(Debt, debt_id)
                    if debt is None or debt.debtor_id != debtor_id:
                        flash('Geçersiz Borç ID.', 'error')
                    else:
                        payment = Payment(
                            debt_id=debt_id,
                            user_id=1,  # Anonim kullanıcı olarak sabit bir ID kullanımı
                            amount=payment_form.amount.data,
                            date=datetime.datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M')
                        )
                        db.session.add(payment)
                        db.session.commit()

                        # Güncel borcu hesapla ve güncelle
                        total_debt = sum(debt.amount for debt in debtor.debts)
                        total_payment = sum(payment.amount for payment in Payment.query.filter(Payment.debt_id.in_([debt.id for debt in debtor.debts])).all())
                        current_debt = total_debt - total_payment
                        flash(f'Tahsilat eklendi. Güncel Borç: {current_debt}', 'success')

                        return redirect(url_for('debtor_detail', debtor_id=debtor_id))
                except Exception as e:
                    db.session.rollback()
                    flash(f'Tahsilat eklenirken bir hata oluştu: {str(e)}', 'error')
            else:
                flash('Form doğrulanamadı. Lütfen tüm alanları doğru doldurduğunuzdan emin olun.', 'error')

    debts = Debt.query.filter_by(debtor_id=debtor_id).all()
    payments = Payment.query.filter(Payment.debt_id.in_([debt.id for debt in debts])).all()
    total_debt = sum(debt.amount for debt in debts)
    total_payment = sum(payment.amount for payment in payments)
    current_debt = total_debt - total_payment

    return render_template('debtor_detail.html', 
                           debtor=debtor, 
                           debt_form=debt_form, 
                           payment_form=payment_form,
                           debts=debts,
                           payments=payments,
                           total_debt=total_debt,
                           total_payment=total_payment,
                           current_debt=current_debt)

@app.route('/delete_debtor/<int:debtor_id>', methods=['POST'])
def delete_debtor(debtor_id):
    debtor = Debtor.query.get_or_404(debtor_id)
    for debt in debtor.debts:
        for payment in debt.payments:
            db.session.delete(payment)
        db.session.delete(debt)
    db.session.delete(debtor)
    db.session.commit()
    return redirect(url_for('cari_takip'))

@app.route('/debtors/<int:debtor_id>/add_debt', methods=['POST'])
def add_debt(debtor_id):
    form = DebtForm()
    if form.validate_on_submit():
        try:
            debt = Debt(
                user_id=1,  # Anonim kullanıcı olarak sabit bir ID kullanımı
                debtor_id=debtor_id,
                amount=form.amount.data,
                due_date=form.date.data
            )
            db.session.add(debt)
            db.session.commit()
            flash('Borç başarıyla eklendi.', 'success')
            return redirect(url_for('debtor_detail', debtor_id=debtor_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Borç eklenirken bir hata oluştu: {str(e)}', 'error')
    return redirect(url_for('debtor_detail', debtor_id=debtor_id))

@app.route('/debtors/<int:debtor_id>/add_payment', methods=['POST'])
def add_payment(debtor_id):
    form = AddPaymentForm()
    if form.validate_on_submit():
        try:
            payment = Payment(
                debt_id=form.debt_id.data,
                amount=form.amount.data,
                date=form.date.data,
                user_id=1  # Anonim kullanıcı olarak sabit bir ID kullanımı
            )
            db.session.add(payment)
            db.session.commit()
            flash('Tahsilat başarıyla eklendi.', 'success')
            return redirect(url_for('debtor_detail', debtor_id=debtor_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Tahsilat eklenirken bir hata oluştu: {str(e)}', 'error')
    return redirect(url_for('debtor_detail', debtor_id=debtor_id))

@app.route('/stok_takip')
def stok_takip():
    stocks = Stock.query.all()
    form = StockForm()
    return render_template('stok_takip.html', stocks=stocks, form=form)

@app.route('/add_stock', methods=['POST'])
def add_stock():
    form = StockForm()
    if form.validate_on_submit():
        try:
            stock = Stock(product=form.product.data, quantity=form.quantity.data, price=form.price.data)
            db.session.add(stock)
            db.session.commit()
            flash('Stok eklendi.', 'success')
            return redirect(url_for('stok_takip'))
        except Exception as e:
            db.session.rollback()
            flash(f'Stok eklenirken bir hata oluştu: {str(e)}', 'error')
    return render_template('stok_takip.html', stocks=Stock.query.all(), form=form)

@app.route('/update_stock/<int:stock_id>', methods=['GET', 'POST'])
def update_stock(stock_id):
    stock = Stock.query.get_or_404(stock_id)
    form = UpdateStockForm()
    if form.validate_on_submit():
        stock.quantity = form.quantity.data
        stock.price = form.price.data
        db.session.commit()
        flash('Stok bilgileri güncellendi.', 'success')
        return redirect(url_for('stok_takip'))
    elif request.method == 'GET':
        form.quantity.data = stock.quantity
        form.price.data = stock.price
    return render_template('update_stock.html', stock=stock, form=form)

@app.route('/delete_stock/<int:stock_id>', methods=['POST'])
def delete_stock(stock_id):
    stock = Stock.query.get_or_404(stock_id)
    db.session.delete(stock)
    db.session.commit()
    flash('Stok silindi.', 'success')
    return redirect(url_for('stok_takip'))

@app.route('/tahsilat', methods=['GET', 'POST'])
def tahsilat():
    form = AddPaymentForm()
    if form.validate_on_submit():
        flash('Tahsilat başarıyla yapıldı.', 'success')
        return redirect(url_for('index'))
    return render_template('tahsilat.html', form=form)

def calculate_current_debt(debtor_id):
    total_debt = db.session.query(db.func.sum(Debt.amount)).filter_by(debtor_id=debtor_id).scalar() or 0
    total_payment = db.session.query(db.func.sum(Payment.amount)).filter_by(debt_id=db.session.query(Debt.id).filter_by(debtor_id=debtor_id)).scalar() or 0
    return total_debt - total_payment

@app.route('/dashboard')
def dashboard():
    current_debt = calculate_current_debt(1)  # Sabit bir kullanıcı ID'si veya anonim
    return render_template('dashboard.html', current_debt=current_debt)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This might be unnecessary if using migration, but left for initial setup.

        users = [
            {'username': 'turhanveteriner', 'email': 'turhanveteriner_unique_new@example.com', 'password': 'sifre1'},
            {'username': 'iyielveteriner', 'email': 'iyielveteriner_1_unique_new@example.com', 'password': 'sifre2'},
            {'username': 'kullanici3_1', 'email': 'kullanici3_1_unique_new@example.com', 'password': 'sifre3'}
        ]

        for user_data in users:
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if existing_user:
                existing_user.email = user_data['email']
            else:
                new_user = User(username=user_data['username'], email=user_data['email'])
                new_user.set_password(user_data['password'])
                db.session.add(new_user)

        db.session.commit()
    
    app.run(debug=True, port=5001, host='0.0.0.0')
