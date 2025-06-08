from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Download, SpeedTest
from auth import admin_required
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
@admin_required
def before_request():
    pass

@admin_bp.route('/')
def dashboard():
    # Get basic stats
    total_users = User.query.count()
    total_downloads = Download.query.count()
    active_downloads = Download.query.filter_by(status='downloading').count()
    completed_downloads = Download.query.filter_by(status='completed').count()
    
    # Get recent downloads
    recent_downloads = Download.query.order_by(Download.created_at.desc()).limit(10).all()
    
    # Get recent speed tests
    recent_speed_tests = SpeedTest.query.order_by(SpeedTest.timestamp.desc()).limit(5).all()
    
    # Get download stats by user
    user_stats = db.session.query(
        User.username,
        db.func.count(Download.id).label('download_count'),
        db.func.sum(Download.downloaded).label('total_downloaded'),
        db.func.sum(Download.uploaded).label('total_uploaded')
    ).join(Download).group_by(User.id).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_downloads=total_downloads,
                         active_downloads=active_downloads,
                         completed_downloads=completed_downloads,
                         recent_downloads=recent_downloads,
                         recent_speed_tests=recent_speed_tests,
                         user_stats=user_stats)

@admin_bp.route('/users')
def users():
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Number of users per page
    
    # Get search query if any
    search_query = request.args.get('search', '').strip()
    query = User.query
    
    if search_query:
        # Search in username or email
        search = f"%{search_query}%"
        query = query.filter(
            (User.username.ilike(search)) | 
            (User.email.ilike(search))
        )
    
    # Order by creation date (newest first)
    query = query.order_by(User.created_at.desc())
    
    # Paginate the results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/users.html', 
                         users=pagination.items,
                         pagination=pagination,
                         search_query=search_query)

@admin_bp.route('/user/<int:user_id>')
def user_details(user_id):
    user = User.query.get_or_404(user_id)
    downloads = Download.query.filter_by(user_id=user_id).order_by(Download.created_at.desc()).all()
    speed_tests = SpeedTest.query.filter_by(user_id=user_id).order_by(SpeedTest.timestamp.desc()).all()
    
    # Calculate user stats
    total_downloads = len(downloads)
    total_downloaded = sum(d.downloaded or 0 for d in downloads)
    total_uploaded = sum(d.uploaded or 0 for d in downloads)
    
    return render_template('admin/user_details.html',
                         user=user,
                         downloads=downloads,
                         speed_tests=speed_tests,
                         total_downloads=total_downloads,
                         total_downloaded=total_downloaded,
                         total_uploaded=total_uploaded)

@admin_bp.route('/downloads')
def downloads():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    status = request.args.get('status')
    user_id = request.args.get('user_id', type=int)
    
    query = Download.query
    
    if status:
        query = query.filter_by(status=status)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    pagination = query.order_by(Download.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    users = User.query.all()
    
    return render_template('admin/downloads.html',
                         downloads=pagination.items,
                         pagination=pagination,
                         users=users,
                         status=status,
                         selected_user_id=user_id)

@admin_bp.route('/speed-tests')
def speed_tests():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    user_id = request.args.get('user_id', type=int)
    
    query = SpeedTest.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    pagination = query.order_by(SpeedTest.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    users = User.query.all()
    
    return render_template('admin/speed_tests.html',
                         speed_tests=pagination.items,
                         pagination=pagination,
                         users=users,
                         selected_user_id=user_id)

@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    # Default settings
    app_settings = {
        'app_name': 'Torrent Downloader',
        'default_download_path': '',
        'max_download_speed': 0,
        'max_upload_speed': 0,
        'max_connections': 200,
        'max_uploads': 8,
        'enable_dht': True,
        'enable_lsd': True,
        'enable_upnp': True,
        'enable_natpmp': True
    }
    
    # Get statistics for the dashboard
    stats = {
        'active_downloads': Download.query.filter_by(status='downloading').count(),
        'total_downloads': Download.query.count(),
        'total_users': User.query.count()
    }
    
    # TODO: Load settings from database or config file
    # For now, we'll use the defaults
    
    if request.method == 'POST':
        # Handle settings update
        # TODO: Save settings to database or config file
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html', 
                         settings=app_settings,
                         stats=stats)
