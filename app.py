from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)


# Store the current video state
video_state = {
    'playing': False,
    'currentTime': 0,
    'video': '/static/videos/your_video.mp4'
}

# Simple admin authentication
ADMIN_PASSWORD = 'your-admin-password'


# Admin session validation + redirect decorator for route
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# Default page for viewers
@app.route('/')
def index():
    return render_template('index.html', video_state=video_state)


# Redirect page from /admin if not logged in the current session
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            return "Invalid password"
    return render_template('admin_login.html')


# Route to admin page - Logic in frontend to check admin authorization and redirect to /admin_login
@app.route('/admin')
@admin_required
def admin():
    return render_template('admin.html', video_state=video_state)


# To handle frontend emit on connect and check if admin is authorized
# Frontend handles redirect to /admin_login if admin_unauthorized is emitted
@socketio.on('admin_connected')
def handle_admin_connected():
    if 'admin' in session:
        emit('admin_authenticated')
    else:
        emit('admin_unauthorized')


# To handle frontend emit of admin updating video state and emit changes to all connected clients
@socketio.on('admin_update_video_state')
def handle_admin_update_video_state(data):
    if 'admin' in session:
        global video_state
        video_state.update(data)
        emit('video_state_updated', video_state, broadcast=True)
    else:
        emit('admin_unauthorized')


# To fetch latest video state
@socketio.on('get_video_state')
def handle_get_video_state():
    emit('video_state_updated', video_state)


if __name__ == '__main__':
    socketio.run(app, debug=True)