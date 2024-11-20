import csv
import hashlib
import os
import secrets
import shutil
import signal
import subprocess
import sys
import zipfile

from flask import render_template, request, jsonify, Blueprint, session

gene_fusion_ML_methods_blueprint = Blueprint(
    "gene_fusion_ML_methods",
    __name__,
    template_folder="templates",
    static_folder='../static'
)


def ensure_dir(directory_path):
    """
    Crea una directory se non esiste già.

    :param directory_path: Il percorso della directory da creare
    """
    try:
        # Crea la directory e tutte le sue sottodirectory se non esiste
        os.makedirs(directory_path, exist_ok=True)
        print(f"Directory '{directory_path}' creata o già esistente.")
    except Exception as e:
        print(f"Errore durante la creazione della directory: {e}")

# Funzione per generare una chiave di sessione unica basata sull'indirizzo IP
def generate_session_key(user_ip):
    random_string = secrets.token_hex(16)
    combined_data = f'{user_ip}_{random_string}-your_secret_string'.encode('utf-8')
    hashed_data = hashlib.sha256(combined_data).hexdigest()

    return hashed_data


# Decoratore before_request per generare la chiave di sessione prima di ogni richiesta
@gene_fusion_ML_methods_blueprint.before_request
def before_request():
    if 'key' not in session:
        user_ip = request.remote_addr
        session['key'] = generate_session_key(user_ip)


@gene_fusion_ML_methods_blueprint.route("/gene_fusion_ML", methods=['GET', 'POST'])
def index():
    # Puoi ora utilizzare session['key'] all'interno di questa rotta
    print("Chiave di sessione:", session['key'])
    user_id = session.get('key')
    return render_template('gene_fusion_ML_method.html', user_id=user_id)