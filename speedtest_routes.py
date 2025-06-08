from flask import Blueprint, jsonify, current_app, request
from flask_login import login_required, current_user
from models import db, SpeedTest
from datetime import datetime
import requests
import threading
import time
import json
import logging

# Initialize blueprint
speedtest_bp = Blueprint('speedtest', __name__)

# Configuration
OPENSPEEDTEST_URL = "http://localhost:3000"  # Default OpenSpeedTest server URL
OPENSPEEDTEST_API_KEY = ""  # Set this if your OpenSpeedTest instance requires an API key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeedTestManager:
    def __init__(self):
        self.active_tests = {}
        self.test_results = {}
        self.lock = threading.Lock()
    
    def start_test(self, user_id, callback=None, app_context=None):
        """Start a new speed test"""
        test_id = f"test_{int(time.time())}_{user_id}"
        
        def run_test():
            try:
                if app_context:
                    app_context.push()
                
                self._update_test_status(test_id, 'running', 'Starting speed test...')
                
                # Check if OpenSpeedTest server is running
                try:
                    response = requests.get(f"{OPENSPEEDTEST_URL}/api/speedtest/servers", timeout=5)
                    if response.status_code != 200:
                        raise Exception("OpenSpeedTest server not available")
                except Exception as e:
                    logger.error(f"OpenSpeedTest server check failed: {str(e)}")
                    self._update_test_status(test_id, 'error', 'Speed test server is not running. Please start the OpenSpeedTest server.')
                    return
                
                # Start the test
                self._update_test_status(test_id, 'running', 'Measuring download speed...')
                
                # In a real implementation, you would use the OpenSpeedTest API
                # For now, we'll simulate the test with a delay
                time.sleep(2)  # Simulate download test
                download_speed = 85.2  # Mbps
                
                self._update_test_status(test_id, 'running', 'Measuring upload speed...')
                time.sleep(2)  # Simulate upload test
                upload_speed = 42.1  # Mbps
                
                # Get server info
                server_info = {
                    'name': 'OpenSpeedTest Server',
                    'location': 'Local',
                    'country': 'Local',
                    'sponsor': 'Self-hosted'
                }
                
                # Save results
                result = {
                    'download': download_speed,
                    'upload': upload_speed,
                    'ping': 12.5,
                    'server': server_info,
                    'timestamp': datetime.utcnow().isoformat(),
                    'bytes_sent': int(upload_speed * 125000),  # Approximate
                    'bytes_received': int(download_speed * 125000),  # Approximate
                    'client': {
                        'ip': request.remote_addr,
                        'isp': 'Local ISP',
                        'isp_rating': '0'
                    }
                }
                
                # Save to database
                try:
                    speed_test = SpeedTest(
                        user_id=user_id,
                        download_speed=download_speed,
                        upload_speed=upload_speed,
                        ping=result['ping'],
                        server_name=server_info['name'],
                        server_location=f"{server_info.get('location', '')}, {server_info.get('country', '')}",
                        timestamp=datetime.utcnow(),
                        ip_address=result['client']['ip'],
                        isp=result['client']['isp'],
                        raw_data=json.dumps(result)
                    )
                    db.session.add(speed_test)
                    db.session.commit()
                except Exception as e:
                    logger.error(f"Error saving speed test to database: {str(e)}")
                    db.session.rollback()
                
                self._update_test_status(test_id, 'completed', 'Speed test completed', result)
                
            except Exception as e:
                logger.error(f"Error in speed test: {str(e)}", exc_info=True)
                self._update_test_status(test_id, 'error', f'Speed test failed: {str(e)}')
            
            if callback:
                callback(test_id, self.test_results.get(test_id, {}).get('status'))
        
        # Start the test in a new thread
        with self.lock:
            self.active_tests[test_id] = {
                'user_id': user_id,
                'start_time': datetime.utcnow(),
                'status': 'queued',
                'message': 'Waiting to start...'
            }
        
        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()
        
        return test_id
    
    def _update_test_status(self, test_id, status, message=None, result=None):
        """Update the status of a test"""
        with self.lock:
            if test_id in self.active_tests:
                self.active_tests[test_id]['status'] = status
                self.active_tests[test_id]['last_updated'] = datetime.utcnow()
                if message:
                    self.active_tests[test_id]['message'] = message
                
                if status in ['completed', 'error']:
                    self.test_results[test_id] = {
                        'status': status,
                        'message': message,
                        'result': result,
                        'test_id': test_id,
                        'user_id': self.active_tests[test_id]['user_id'],
                        'start_time': self.active_tests[test_id]['start_time'],
                        'end_time': datetime.utcnow()
                    }
                    # Remove from active tests after a delay
                    del self.active_tests[test_id]
    
    def get_test_status(self, test_id):
        """Get the status of a test"""
        with self.lock:
            if test_id in self.active_tests:
                return {
                    'status': self.active_tests[test_id]['status'],
                    'message': self.active_tests[test_id].get('message', ''),
                    'test_id': test_id,
                    'user_id': self.active_tests[test_id]['user_id'],
                    'start_time': self.active_tests[test_id]['start_time'].isoformat(),
                    'is_active': True
                }
            elif test_id in self.test_results:
                result = self.test_results[test_id].copy()
                result['start_time'] = result['start_time'].isoformat()
                result['end_time'] = result['end_time'].isoformat()
                result['is_active'] = False
                if 'result' in result and 'user_id' not in result:
                    result['user_id'] = result.get('result', {}).get('user_id')
                return result
            return None

# Initialize the speed test manager
speed_test_manager = SpeedTestManager()

def format_speed(speed_bps):
    """Convert speed in bits per second to a human-readable format"""
    for unit in ['bps', 'Kbps', 'Mbps', 'Gbps']:
        if speed_bps < 1000 or unit == 'Gbps':
            return f"{speed_bps:.2f} {unit}"
        speed_bps /= 1000
    return f"{speed_bps:.2f} bps"

# Route handlers
@speedtest_bp.route('/start', methods=['POST'])
@login_required
def start_speed_test():
    """Start a new speed test"""
    try:
        # Check if there's already a test in progress for this user
        for test_id, test_info in speed_test_manager.active_tests.items():
            if test_info['user_id'] == current_user.id and test_info['status'] == 'running':
                return jsonify({
                    'status': 'already_running',
                    'message': 'A speed test is already in progress',
                    'test_id': test_id
                })
        
        # Start a new test
        test_id = speed_test_manager.start_test(
            current_user.id,
            app_context=current_app.app_context()
        )
        
        return jsonify({
            'status': 'started',
            'test_id': test_id,
            'message': 'Speed test started'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error starting speed test: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@speedtest_bp.route('/status/<test_id>', methods=['GET'])
@login_required
def get_speed_test_status(test_id):
    """Get the status of a speed test"""
    try:
        # Check if the test exists in the database
        test = SpeedTest.query.filter_by(id=test_id, user_id=current_user.id).first()
        if test:
            return jsonify({
                'status': 'completed',
                'test_id': str(test.id),
                'download': test.download_speed,
                'upload': test.upload_speed,
                'ping': test.ping,
                'server': test.server_name,
                'ip_address': test.ip_address,
                'isp': test.isp,
                'timestamp': test.timestamp.isoformat(),
                'is_active': False
            })
        
        # Check if it's an active test
        status = speed_test_manager.get_test_status(test_id)
        if status:
            if status.get('user_id') != current_user.id:
                return jsonify({'status': 'error', 'message': 'Access denied'}), 403
            return jsonify(status)
        
        return jsonify({'status': 'not_found', 'message': 'Test not found'}), 404
        
    except Exception as e:
        logger.error(f"Error getting test status: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@speedtest_bp.route('/history', methods=['GET'])
@login_required
def get_speed_test_history():
    """Get the speed test history for the current user"""
    try:
        # Get the most recent 50 tests for the current user
        tests = SpeedTest.query.filter_by(user_id=current_user.id)\
            .order_by(SpeedTest.timestamp.desc())\
            .limit(50).all()
        
        return jsonify([{
            'id': str(test.id),
            'download': test.download_speed,
            'upload': test.upload_speed,
            'ping': test.ping,
            'server': test.server_name,
            'ip_address': test.ip_address,
            'isp': test.isp,
            'timestamp': test.timestamp.isoformat(),
            'is_active': False
        } for test in tests])
        
    except Exception as e:
        logger.error(f"Error getting test history: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500
