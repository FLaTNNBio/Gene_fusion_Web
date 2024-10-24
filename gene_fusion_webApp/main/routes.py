import hashlib
import os
import random
import secrets

from flask import render_template, request, jsonify, Blueprint, redirect, url_for, current_app, session, send_file

import app

main_blueprint = Blueprint(
    "main",
    __name__,
    template_folder="templates",
    static_folder='../static'
)


# Funzione per generare una chiave di sessione unica basata sull'indirizzo IP
def generate_session_key(user_ip):
    random_string = secrets.token_hex(16)
    combined_data = f'{user_ip}_{random_string}-your_secret_string'.encode('utf-8')
    hashed_data = hashlib.sha256(combined_data).hexdigest()

    return hashed_data


# Decoratore before_request per generare la chiave di sessione prima di ogni richiesta
@main_blueprint.before_request
def before_request():
    if 'key' not in session:
        user_ip = request.remote_addr
        session['key'] = generate_session_key(user_ip)



@main_blueprint.route("/", methods=['GET', 'POST'])
def HomePage():
    # Puoi ora utilizzare session['key'] all'interno di questa rotta
    print("Chiave di sessione:", session['key'])
    user_id = session.get('key')
    return render_template('HomePage.html')


