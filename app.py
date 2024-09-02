from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

# Store the current video state
# TBD: Allow changing of video path through admin portal
video_state = {
    'playing': False,
    'currentTime': 0,
    'video': '/static/videos/your_video.mp4'
}

# Simple admin authentication
ADMIN_PASSWORD = 'your-admin-password'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html', video_state=video_state)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            return "Invalid password"
    return render_template('admin_login.html')

@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html', video_state=video_state)

@socketio.on('admin_update_video_state')
def handle_admin_update_video_state(data):
    if 'admin' in session:
        global video_state
        video_state.update(data)
        emit('video_state_updated', video_state, broadcast=True)

@socketio.on('get_video_state')
def handle_get_video_state():
    emit('video_state_updated', video_state)

@socketio.on('admin_connected')
def handle_admin_connected():
    if 'admin' in session:
        emit('admin_authenticated')
    else:
        emit('admin_unauthorized')

if __name__ == '__main__':
    socketio.run(app, debug=True)