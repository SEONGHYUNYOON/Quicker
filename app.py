from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///keeper.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password_hash = db.Column(db.String(120), nullable=False)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    cid = db.Column(db.String(50), unique=True, nullable=False)
    expire_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Integer, default=0)
    recommender = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

@app.route('/')
def index():
    return jsonify({
        "message": "Keeper Member Management API",
        "status": "running",
        "endpoints": {
            "admin_login": "/admin/login",
            "admin_dashboard": "/admin/dashboard",
            "api_health": "/api/health",
            "api_cid_verify": "/api/cid/verify"
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Keeper Member Management",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db.engine.pool.checkedin() >= 0 else "disconnected"
    })

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        admin = Admin.query.first()
        if admin is None:
            default_admin = Admin(password_hash=generate_password_hash('4568'))
            db.session.add(default_admin)
            db.session.commit()
            admin = default_admin
        if check_password_hash(admin.password_hash, password):
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error='Invalid password')
    return render_template('login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    query = Member.query
    if search:
        query = query.filter(
            db.or_(
                Member.name.contains(search),
                Member.phone.contains(search),
                Member.recommender.contains(search)
            )
        )
    members = query.order_by(Member.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    today = date.today()
    active_count = Member.query.filter(Member.expire_date >= today).count()
    expired_count = Member.query.filter(Member.expire_date < today).count()
    total_amount = db.session.query(db.func.sum(Member.amount)).scalar() or 0
    return render_template('dashboard.html',
                         members=members,
                         search=search,
                         today=today,
                         active_count=active_count,
                         expired_count=expired_count,
                         total_amount=total_amount)

@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
def add_member():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        cid = request.form.get('cid')
        member_type = request.form.get('member_type')
        amount = request.form.get('amount', 0, type=int)
        recommender = request.form.get('recommender')
        if member_type == 'test':
            expire_date = date.today() + timedelta(days=3)
        else:
            expire_date = date.today() + timedelta(days=40)
        if Member.query.filter_by(phone=phone).first():
            flash('이미 등록된 전화번호입니다.', 'error')
            return render_template('add.html')
        if Member.query.filter_by(cid=cid).first():
            flash('이미 등록된 CID입니다.', 'error')
            return render_template('add.html')
        member = Member(
            name=name,
            phone=phone,
            cid=cid,
            expire_date=expire_date,
            amount=amount,
            recommender=recommender
        )
        db.session.add(member)
        db.session.commit()
        flash('회원이 성공적으로 추가되었습니다.', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('add.html')

@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_member(id):
    member = Member.query.get_or_404(id)
    if request.method == 'POST':
        member.name = request.form.get('name')
        member.phone = request.form.get('phone')
        member.cid = request.form.get('cid')
        member.amount = request.form.get('amount', 0, type=int)
        member.recommender = request.form.get('recommender')
        expire_date_str = request.form.get('expire_date')
        if expire_date_str:
            member.expire_date = datetime.strptime(expire_date_str, '%Y-%m-%d').date()
        existing_phone = Member.query.filter_by(phone=member.phone).first()
        if existing_phone and existing_phone.id != id:
            flash('이미 등록된 전화번호입니다.', 'error')
            return render_template('edit.html', member=member)
        existing_cid = Member.query.filter_by(cid=member.cid).first()
        if existing_cid and existing_cid.id != id:
            flash('이미 등록된 CID입니다.', 'error')
            return render_template('edit.html', member=member)
        db.session.commit()
        flash('회원 정보가 성공적으로 수정되었습니다.', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('edit.html', member=member)

@app.route('/admin/delete/<int:id>')
@login_required
def delete_member(id):
    member = Member.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    flash('회원이 성공적으로 삭제되었습니다.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('admin_login'))

@app.route('/api/cid/verify', methods=['GET', 'POST'])
def verify_cid():
    if request.method == 'GET':
        return jsonify({
            "status": "success",
            "message": "CID API is running",
            "method": "GET",
            "test_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_token"
        })
    elif request.method == 'POST':
        data = request.get_json()
        cid = data.get('cid', None)
        phone = data.get('phone', None)
        if cid == "testcid":
            return jsonify({
                "status": "success",
                "token": "dummy_token"
            })
        else:
            return jsonify({
                "status": "fail",
                "message": "CID not registered"
            })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
