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

from gene_fusion_webApp.input_file_validator import validate_chimeric_fingerprint_format, \
    validate_non_chimeric_fingerprint_format

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


def clear_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)  # Rimuove ricorsivamente la directory e tutto il suo contenuto


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


# Controlli per la validazione degli input dell'utente
@gene_fusion_ML_methods_blueprint.route("/validate_files_ML", methods=["POST"])
def validate_files_ML():
    # Ottieni i file dal request
    execution_type = request.form.get("executionType")

    if execution_type == "MML_experiment":
        MML_chimeric_fingerprint_file = request.files.get("MML_chimeric_fingerprint_file")
        MML_non_chimeric_fingerprint_file = request.files.get("MML_non_chimeric_fingerprint_file")

        # Verifica che i file siano presenti e validi
        if not MML_chimeric_fingerprint_file or not MML_non_chimeric_fingerprint_file:
            return jsonify({"success": False, "message": "Both Chimeric and Non-Chimeric datasets are required."})

        chimeric_content_MML = MML_chimeric_fingerprint_file.read().decode('utf-8')
        non_chimeric_content_MML = MML_non_chimeric_fingerprint_file.read().decode('utf-8')
        is_valid_chimeric_MML = validate_chimeric_fingerprint_format(chimeric_content_MML)
        is_valid_non_chimeric_MML = validate_non_chimeric_fingerprint_format(non_chimeric_content_MML)

        if  is_valid_chimeric_MML:
            return jsonify({"success": False, "message": "Invalid Chimeric dataset format."})

        if  is_valid_non_chimeric_MML:
            return jsonify({"success": False, "message": "Invalid Non-Chimeric dataset format."})

    elif execution_type == "MGE_experiment":
        MGE_chimeric_fingerprint_file = request.files.get("MGE_chimeric_fingerprint_file")
        MGE_non_chimeric_fingerprint_file = request.files.get("MGE_non_chimeric_fingerprint_file")

        # Verifica che i file siano presenti e validi
        if not MGE_chimeric_fingerprint_file or not MGE_non_chimeric_fingerprint_file:
            return jsonify({"success": False, "message": "Both Chimeric and Non-Chimeric datasets are required."})

        chimeric_content_MGE = MGE_chimeric_fingerprint_file.read().decode('utf-8')
        non_chimeric_content_MGE = MGE_non_chimeric_fingerprint_file.read().decode('utf-8')

        is_valid_chimeric_MGE = validate_chimeric_fingerprint_format(chimeric_content_MGE)
        is_valid_non_chimeric_MGE = validate_non_chimeric_fingerprint_format(non_chimeric_content_MGE)

        if  is_valid_chimeric_MGE:
            return jsonify({"success": False, "message": "Invalid Chimeric dataset format."})

        if  is_valid_non_chimeric_MGE:
            return jsonify({"success": False, "message": "Invalid Non-Chimeric dataset format."})

    return jsonify({"success": True, "message": "Files are valid."})

@gene_fusion_ML_methods_blueprint.route('/execute_command_ML/<int:command_id>', methods=['POST'])
def execute_command_ML(command_id):
    global cancellation_requested
    process = None

    MML_chimeric_fingerprint_file = request.files.get("MML_chimeric_fingerprint_file")
    MML_non_chimeric_fingerprint_file = request.files.get("MML_non_chimeric_fingerprint_file")


    MGE_chimeric_fingerprint_file = request.files.get("MGE_chimeric_fingerprint_file")
    MGE_non_chimeric_fingerprint_file = request.files.get("MGE_non_chimeric_fingerprint_file")

    # Gene fusion ML execution dir
    gene_fusion_ML_dir = os.path.join(os.getcwd(), 'gene_fusion_ML/')
    src_execution_dir = os.path.join(gene_fusion_ML_dir, 'src/')
    MML_execution_dir = os.path.join(src_execution_dir, 'MML_experiment.py')
    MGE_execution_dir = os.path.join(src_execution_dir, 'MGE_experiment.py')

    # Gene fusion ML base dir
    training_directory = os.path.join(gene_fusion_ML_dir, 'src', 'training/')
    testing_directory = os.path.join(gene_fusion_ML_dir, 'src', 'testing/')

    dataset_input_dir = os.path.join(gene_fusion_ML_dir, 'dataset/')
    models_mml_dir = os.path.join(gene_fusion_ML_dir, 'models_mml/')
    models_mge_dir = os.path.join(gene_fusion_ML_dir, 'models_mge/')

    download_dir = os.path.join(os.getcwd(), 'gene_fusion_webApp', 'static', 'downloads/')

    ensure_dir(training_directory)
    ensure_dir(testing_directory)
    ensure_dir(dataset_input_dir)

    clear_directory(training_directory)
    clear_directory(testing_directory)
    clear_directory(dataset_input_dir)

    # Salva i file caricati
    if MML_chimeric_fingerprint_file:
        chimeric_file_path = os.path.join(dataset_input_dir, MML_chimeric_fingerprint_file.filename)
        MML_chimeric_fingerprint_file.save(chimeric_file_path)
    if MML_non_chimeric_fingerprint_file:
        non_chimeric_file_path = os.path.join(dataset_input_dir, MML_non_chimeric_fingerprint_file.filename)
        MML_non_chimeric_fingerprint_file.save(non_chimeric_file_path)

    if MGE_chimeric_fingerprint_file:
        chimeric_file_path = os.path.join(dataset_input_dir, MGE_chimeric_fingerprint_file.filename)
        MGE_chimeric_fingerprint_file.save(chimeric_file_path)
    if MGE_non_chimeric_fingerprint_file:
        non_chimeric_file_path = os.path.join(dataset_input_dir, MGE_non_chimeric_fingerprint_file.filename)
        MGE_non_chimeric_fingerprint_file.save(non_chimeric_file_path)
    print(MML_chimeric_fingerprint_file)
    try:
        command_args = []
        # Configura i parametri in base al command_id
        if command_id == 1:  # Comando per MML_experiment.py
            print("Eseguendo Comando 1: MLL Experiment")
            command_args = [
                MML_execution_dir,
                "--filename_fuse", os.path.join(dataset_input_dir, MML_chimeric_fingerprint_file.filename),
                "--filename_no_fuse", os.path.join(dataset_input_dir, MML_non_chimeric_fingerprint_file.filename),
                "--k", "4"
            ]

        elif command_id == 2:  # Comando per MGE_experiment.py
            print("Eseguendo Comando 2: MGE Experiment")
            command_args = [
                MGE_execution_dir,
                "--filename_fuse", os.path.join(dataset_input_dir, MGE_chimeric_fingerprint_file.filename),
                "--filename_no_fuse", os.path.join(dataset_input_dir, MGE_non_chimeric_fingerprint_file.filename),
                "--k", "4"
            ]


        # Log di debug
        print(f"Eseguendo comando con command_id={command_id}, args={command_args}")


        if command_id == 1 or command_id == 2:
            # Esegui il comando
            process = subprocess.Popen(
                [r'C:\Users\eduk4\PycharmProjects\Gene_fusion_Web\venv\Scripts\python.exe'] + command_args,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Attendi il termine del processo
            stdout, stderr = process.communicate()
            print(f"Comando eseguito, stdout={stdout.decode('utf-8')}, stderr={stderr.decode('utf-8')}")

        # Gestione output comando MML
        if process.returncode == 0 and command_id == 1:
            # Cerca i file del modello e i file di prestazioni
            model_files = []
            performance_files = []

            # Trova i file del modello e le prestazioni
            for filename in os.listdir(models_mml_dir):
                file_path = os.path.join(models_mml_dir, filename)
                if os.path.isfile(file_path):
                    # Controlla se il file è un modello (usiamo un semplice criterio, come l'estensione .pickle)
                    if filename.endswith('.pth'):
                        model_files.append(file_path)

            # Verifica se sono stati trovati file
            if not model_files and not performance_files:
                return jsonify({'success': False, 'error': 'Nessun file di modello o di prestazione trovato.'})

                # Crea uno zip con i file trovati
            zip_filename = os.path.join(download_dir, 'model_MML_files.zip')
            with zipfile.ZipFile(zip_filename, 'w') as zip_file:
                # Aggiungi i file del modello
                for model_file in model_files:
                    zip_file.write(model_file, os.path.basename(model_file))

                # Aggiungi i file di prestazioni
                for performance_file in performance_files:
                    zip_file.write(performance_file, os.path.basename(performance_file))

            # Restituisci l'URL del file zip al frontend
            download_url = f'/static/downloads/model_MML_files.zip'
            return jsonify({'success': True, 'download_url': download_url})

        # Gestione output comando MGE
        if process.returncode == 0 and command_id == 2:
            # Cerca i file del modello e i file di prestazioni
            model_files = []
            performance_files = []

            # Trova i file del modello e le prestazioni
            for filename in os.listdir(models_mge_dir):
                file_path = os.path.join(models_mge_dir, filename)
                if os.path.isfile(file_path):
                    # Controlla se il file è un modello (usiamo un semplice criterio, come l'estensione .pickle)
                    if filename.endswith('.pth'):
                        model_files.append(file_path)

            # Verifica se sono stati trovati file
            if not model_files and not performance_files:
                return jsonify({'success': False, 'error': 'Nessun file di modello o di prestazione trovato.'})

                # Crea uno zip con i file trovati
            zip_filename = os.path.join(download_dir, 'model_MGE_files.zip')
            with zipfile.ZipFile(zip_filename, 'w') as zip_file:
                # Aggiungi i file del modello
                for model_file in model_files:
                    zip_file.write(model_file, os.path.basename(model_file))

                # Aggiungi i file di prestazioni
                for performance_file in performance_files:
                    zip_file.write(performance_file, os.path.basename(performance_file))

            # Restituisci l'URL del file zip al frontend
            download_url = f'/static/downloads/model_MGE_files.zip'
            return jsonify({'success': True, 'download_url': download_url})

        # Usa il contesto `with` per avviare e chiudere automaticamente il processo
        with subprocess.Popen(
                [sys.executable] + command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ) as process:
            try:
                # Attendi con un timeout per evitare processi bloccati
                stdout, stderr = process.communicate(timeout=300)  # Timeout di 5 minuti
            except subprocess.TimeoutExpired:
                process.kill()  # Interrompi il processo se supera il timeout
                stdout, stderr = process.communicate()

            if process.returncode == 0:
                print(f"Comando eseguito correttamente: {stdout.decode('utf-8')}")
                # Continua con la logica di successo
            else:
                print(f"Errore durante l'esecuzione del comando: {stderr.decode('utf-8')}")
                return jsonify({'success': False, 'error': stderr.decode('utf-8')})



    except Exception as e:
        print(f"Errore durante l'esecuzione del comando: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        # Controlla se il processo è ancora aperto e chiudilo
        if process:
            process.terminate()
            process = None
