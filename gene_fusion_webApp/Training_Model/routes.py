import hashlib
import secrets


from flask import render_template, request, jsonify, Blueprint, redirect, url_for, current_app, session, send_file
import app

training_blueprint = Blueprint(
    "training",
    __name__,
    template_folder="templates",
    static_folder='../static'
)

cancellation_requested = False
file_ready = False


# Funzione per generare una chiave di sessione unica basata sull'indirizzo IP
def generate_session_key(user_ip):
    random_string = secrets.token_hex(16)
    combined_data = f'{user_ip}_{random_string}-your_secret_string'.encode('utf-8')
    hashed_data = hashlib.sha256(combined_data).hexdigest()

    return hashed_data

# Decoratore before_request per generare la chiave di sessione prima di ogni richiesta
@training_blueprint.before_request
def before_request():
    if 'key' not in session:
        user_ip = request.remote_addr
        session['key'] = generate_session_key(user_ip)


@training_blueprint.route("/training_model", methods=['GET', 'POST'])
def index():
    # Puoi ora utilizzare session['key'] all'interno di questa rotta
    print("Chiave di sessione:", session['key'])
    user_id = session.get('key')
    return render_template('training.html', user_id=user_id)
