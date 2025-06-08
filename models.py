from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    downloads = db.relationship('Download', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class TorrentFile(db.Model):
    __tablename__ = 'torrent_files'
    
    id = db.Column(db.Integer, primary_key=True)
    info_hash = db.Column(db.String(40), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    size = db.Column(db.BigInteger)  # Size in bytes
    files = db.Column(db.JSON)  # Store file list as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    downloads = db.relationship('Download', backref='torrent', lazy=True)

class Download(db.Model):
    __tablename__ = 'downloads'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    torrent_id = db.Column(db.Integer, db.ForeignKey('torrent_files.id'), nullable=False)
    save_path = db.Column(db.String(512), nullable=False)
    status = db.Column(db.String(20), default='downloading')  # downloading, completed, paused, error
    progress = db.Column(db.Float, default=0.0)  # 0.0 to 100.0
    download_speed = db.Column(db.Float)  # bytes per second
    upload_speed = db.Column(db.Float)  # bytes per second
    uploaded = db.Column(db.BigInteger, default=0)  # bytes uploaded
    downloaded = db.Column(db.BigInteger, default=0)  # bytes downloaded
    ratio = db.Column(db.Float, default=0.0)  # upload / download ratio
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def update_progress(self, progress, downloaded, uploaded, download_speed, upload_speed):
        self.progress = progress
        self.downloaded = downloaded
        self.uploaded = uploaded
        self.download_speed = download_speed
        self.upload_speed = upload_speed
        self.ratio = uploaded / downloaded if downloaded > 0 else 0
        if progress >= 100 and self.status != 'completed':
            self.status = 'completed'
            self.completed_at = datetime.utcnow()
        db.session.commit()

class SpeedTest(db.Model):
    __tablename__ = 'speed_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    download_speed = db.Column(db.Float)  # in Mbps
    upload_speed = db.Column(db.Float)  # in Mbps
    ping = db.Column(db.Float)  # in ms
    server = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='speed_tests')
