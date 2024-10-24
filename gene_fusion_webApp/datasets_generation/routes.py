# Importa le librerie necessarie
import hashlib
import io
import os
import random
import re
import secrets
import zipfile


from gene_fusion_webApp.datasets_generation.directory_utility import *
from gene_fusion_webApp.datasets_generation.fusim import execute_fusim_script
from gene_fusion_webApp.datasets_generation.gen_dataset import execute_gen_dataset_script

from flask import render_template, request, jsonify, Blueprint, redirect, url_for, current_app, session, send_file

dataset_generation_blueprint = Blueprint(
    "dataset_generation",
    __name__,
    template_folder="templates",
    static_folder='../static'
)

cancellation_requested = False
file_ready = False
name_file_dataset_generated=''

# Funzione per generare una chiave di sessione unica basata sull'indirizzo IP
def generate_session_key(user_ip):
    random_string = secrets.token_hex(16)
    combined_data = f'{user_ip}_{random_string}-your_secret_string'.encode('utf-8')
    hashed_data = hashlib.sha256(combined_data).hexdigest()

    return hashed_data


# Decoratore before_request per generare la chiave di sessione prima di ogni richiesta
@dataset_generation_blueprint.before_request
def before_request():
    if 'key' not in session:
        user_ip = request.remote_addr
        session['key'] = generate_session_key(user_ip)


@dataset_generation_blueprint.route("/generation_dataset", methods=['GET', 'POST'])
def index():
    # Puoi ora utilizzare session['key'] all'interno di questa rotta
    print("Chiave di sessione:", session['key'])
    user_id = session.get('key')
    return render_template('gen_dataset.html', user_id=user_id)



# @main_blueprint.route('/download_file')
# def download_file():
#     # Genera il contenuto dei file FASTA
#     file1_content = ">seq1\nAGCTAGCTAGCTAGCTA\n"
#     file2_content = ">seq2\nTCGATCGATCGATCGAT\n"
#
#     # Verifica se ci sono dati
#     if not file1_content and not file2_content:
#         return jsonify({'error': 'No data available'}), 400
#
#     # Crea un file ZIP in memoria
#     zip_buffer = io.BytesIO()
#     with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
#         zip_file.writestr('file1.fasta', file1_content)
#         zip_file.writestr('file2.fasta', file2_content)
#
#     zip_buffer.seek(0)
#
#     return send_file(zip_buffer, as_attachment=True, download_name='files.zip', mimetype='application/zip')


# Richiesta get per lo script loading_bar.js
@dataset_generation_blueprint.route('/get_completion_percentage_fusim', methods=['GET'])
def get_completion_percentage_fusim():
    # Ottieni le informazioni dal contesto dell'applicazione
    completion_percentage_fusim = current_app.config.get('completion_percentage_fusim', 0)
    estimated_time_elapsed_fusim = current_app.config.get('estimated_time_elapsed_fusim', 1)

    # Crea un oggetto JSON con la percentuale di completamento e il tempo stimato
    response_data = {
        'completion_percentage_fusim': completion_percentage_fusim,
        'estimated_time_elapsed_fusim': estimated_time_elapsed_fusim
    }

    return jsonify(response_data)


# Richiesta get per lo script loading_bar.js
@dataset_generation_blueprint.route('/get_completion_percentage_genDataset', methods=['GET'])
def get_completion_percentage_gen_dataset():
    # Ottieni le informazioni dal contesto dell'applicazione
    completion_percentage_genDataset = current_app.config.get('completion_percentage_genDataset', 0)
    estimated_time_elapsed_genDataset = current_app.config.get('estimated_time_elapsed_genDataset', 1)

    # Crea un oggetto JSON con la percentuale di completamento e il tempo stimato
    response_data = {
        'completion_percentage_genDataset': completion_percentage_genDataset,
        'estimated_time_elapsed_genDataset': estimated_time_elapsed_genDataset
    }

    return jsonify(response_data)

# Riceve il nome dei file da scaricare da generazione_dataset.py
@dataset_generation_blueprint.route('/get_name_file', methods=['POST'])
def get_name_file():
    global file_ready, name_file_dataset_generated, zip_buffer_file_global
    try:
        data = request.get_json()

        # Verifica se il nome del file è già stato assegnato
        if name_file_dataset_generated == '':
            name_file_dataset_generated = data.get('name_file', 0)

        # Ottieni il contesto dell'applicazione
        app_config = current_app.config

        # Imposta il nome del file nel contesto dell'applicazione
        app_config['name_file'] = name_file_dataset_generated
        file_path = os.path.join("gene_fusion_webApp/static/uploads", name_file_dataset_generated)

        # Estrai il numero dal nome del file (per esempio, estrae "123" da "dataset_chimeric_123.fastq")
        match = re.search(r'_(\d+)\.fastq$', name_file_dataset_generated)
        if not match:
            return jsonify({'success': False, 'error': 'No number found in name_file'}), 400
        number = match.group(1)  # Estrae il numero

        try:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                # Aggiungi solo i file .fastq che contengono lo stesso numero
                for filename in os.listdir("gene_fusion_webApp/static/uploads"):
                    if filename.endswith('.fastq') and number in filename:
                        file_path = os.path.join("gene_fusion_webApp/static/uploads", filename)
                        with open(file_path, 'r') as f:
                            zip_file.writestr(filename, f.read())

            zip_buffer.seek(0)
            app_config['ZIP_BUFFER'] = zip_buffer
            zip_buffer_file_global = zip_buffer
            file_ready = True

        except Exception as e:
            file_ready = False
            app_config['ZIP_ERROR'] = str(e)

        return jsonify({'success': True, 'name_file': name_file_dataset_generated})

    except Exception as e:
        # Restituisci un messaggio di errore nella risposta JSON
        return jsonify({'success': False, 'error': str(e)}), 500


@dataset_generation_blueprint.route('/download_file')
def download_file():
    global file_ready, name_file_dataset_generated

    # Controlla se il file è pronto
    if not file_ready:
        return jsonify({'error': 'Files not ready'}), 400

    try:
        # Estrai il numero dal nome del file (per esempio, "123" da "dataset_chimeric_123.fastq")
        match = re.search(r'_(\d+)\.fastq$', name_file_dataset_generated)
        if not match:
            return jsonify({'error': 'No number found in name_file'}), 400
        number = match.group(1)  # Estrae il numero

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            # Aggiungi solo i file .fastq che contengono lo stesso numero
            for filename in os.listdir("gene_fusion_webApp/static/downloads"):
                if filename.endswith('.fastq') and number in filename:
                    file_path = os.path.join("gene_fusion_webApp/static/downloads", filename)
                    with open(file_path, 'r') as f:
                        zip_file.writestr(filename, f.read())

            # Aggiungi anche il file custom_panel se esiste con lo stesso numero
            custom_panel_filename = f"custom_panel_{number}.txt"
            custom_panel_path = os.path.join("gene_fusion_webApp/static/downloads", custom_panel_filename)

            if os.path.exists(custom_panel_path):
                with open(custom_panel_path, 'r') as custom_panel_file:
                    zip_file.writestr(custom_panel_filename, custom_panel_file.read())
        # Resetta il buffer alla posizione iniziale
        zip_buffer.seek(0)

        # Imposta il nome del file per il download
        random_number = random.randint(1, 1000)
        return send_file(zip_buffer, as_attachment=True, download_name='files' + str(random_number) + ".zip",
                         mimetype='application/zip')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dataset_generation_blueprint.route('/check_status')
def check_status():
    # Ottieni il contesto dell'applicazione
    app_config = current_app.config
    if file_ready:
        return jsonify({'status': 'ready'}), 200
    elif app_config == 'ZIP_ERROR':
        return jsonify({'status': 'error', 'message': app_config['ZIP_ERROR']}), 500
    else:
        return jsonify({'status': 'not ready'}), 202

# Riceve le percentuali di completamento da execute.py
@dataset_generation_blueprint.route('/update_completion_percentage_fusim/<user_id>', methods=['POST'])
def update_completion_percentage_fusim(user_id):
    try:
        data = request.get_json()

        new_completion_percentage = data.get('completion_percentage_fusim', 0)
        estimated_time_elapsed = data.get('estimated_time_elapsed_fusim', 1)

        # Ottieni il contesto dell'applicazione
        app_config = current_app.config

        app_config['completion_percentage_fusim'] = new_completion_percentage
        app_config['estimated_time_elapsed_fusim'] = estimated_time_elapsed
        print(
            f"Percentuale di completamento e tempo rimanente aggiornato: {new_completion_percentage}% {estimated_time_elapsed}")

        # Includi la percentuale di completamento ed il tempo stimato nella risposta JSON
        return jsonify({'success': True, 'completion_percentage_fusim': new_completion_percentage,
                        'estimated_time_elapsed_fusim': estimated_time_elapsed})

    except Exception as e:
        print(f"Errore durante l'aggiornamento della percentuale di completamento: {str(e)}")

        # Restituisci un messaggio di errore nella risposta JSON
        return jsonify({'success': False, 'error': str(e)}), 500


@dataset_generation_blueprint.route('/update_completion_percentage_genDataset/<user_id>', methods=['POST'])
def update_completion_percentage_genDataset(user_id):
    try:
        data = request.get_json()

        new_completion_percentage = data.get('completion_percentage_genDataset', 0)
        estimated_time_elapsed = data.get('estimated_time_elapsed_genDataset', 1)

        # Ottieni il contesto dell'applicazione
        app_config = current_app.config

        app_config['completion_percentage_genDataset'] = new_completion_percentage
        app_config['estimated_time_elapsed_genDataset'] = estimated_time_elapsed
        print(
            f"Percentuale di completamento e tempo rimanente aggiornato: {new_completion_percentage}% {estimated_time_elapsed}")

        # Includi la percentuale di completamento ed il tempo stimato nella risposta JSON
        return jsonify({'success': True, 'completion_percentage_genDataset': new_completion_percentage,
                        'estimated_time_elapsed_genDataset': estimated_time_elapsed})

    except Exception as e:
        print(f"Errore durante l'aggiornamento della percentuale di completamento: {str(e)}")

        # Restituisci un messaggio di errore nella risposta JSON
        return jsonify({'success': False, 'error': str(e)}), 500






@dataset_generation_blueprint.route('/save-custom-panel', methods=['POST'])
def save_custom_panel():
    global cancellation_requested,file_ready
    try:
        # Riceve da uploadFile.js la lista di geni selezionata dall'utente
        text_data = request.json['data']

        # ------------------------------------------------------------------------------------------------
        #                                   Generazione file fusim

        # Imposta la fusim directory per scaricare custom_panel.txt
        fusim_user_directory = move_to_user_directory_fusim()

        # Imposta il percorso del file
        custom_panel_in_fusim_directory = os.path.join(fusim_user_directory, 'custom_panel.txt')

        # Verifica se il file esiste già
        if not os.path.exists(custom_panel_in_fusim_directory):
            # Se il file non esiste, crea la directory (se necessario)
            os.makedirs(os.path.dirname(custom_panel_in_fusim_directory), exist_ok=True)

        # Scrivi la stringa di testo nel file
        with open(custom_panel_in_fusim_directory, 'w') as file1:
            file1.write(text_data)

        # flag di disponibilità download su false
        file_ready = False

        # Elimino i vecchi file (chimeric e non chimeric) da uploads
        delete_files_in_directory("gene_fusion_webApp/static/downloads")

        # [Eseguo lo script fusim dopo aver salvato il file]
        if not cancellation_requested:
            execute_fusim_script()
        # ------------------------------------------------------------------------------------------------
        #                                        Generazione Dataset

        # Imposta la directory "Generazione_dataset" per scaricare custom_panel.txt
        generazione_dataset_user_directory = move_to_user_directory_Gen_dataset()

        custom_panel_in_gen_dataset = os.path.join(generazione_dataset_user_directory, 'custom_panel.txt')

        # Verifica se il file esiste già
        if not os.path.exists(custom_panel_in_gen_dataset):
            # Se il file non esiste, crea la directory (se necessario)
            os.makedirs(os.path.dirname(custom_panel_in_gen_dataset), exist_ok=True)

        # Salva il file
        with open(custom_panel_in_gen_dataset, 'w') as file2:
            file2.write(text_data)



        # [Eseguo lo script generazione dataset dopo aver salvato il file]
        if not cancellation_requested:
            execute_gen_dataset_script()


        return jsonify({'message': 'File salvato con successo'}), 200

    except Exception as e:
        print(f'Errore durante il salvataggio del file: {str(e)}')

        return jsonify({'error': 'Errore interno del server'}), 500


# Funzione per richiedere l'annullamento del comando(subprocess)
@dataset_generation_blueprint.route('/request_cancellation', methods=['POST'])
def request_cancellation():
    global completion_percentage
    global estimated_time_elapsed
    global cancellation_requested

    completion_percentage = 0
    estimated_time_elapsed = ""
    # Ottieni il contesto dell'applicazione
    app_config = current_app.config

    app_config['completion_percentage_genDataset'] = 0
    app_config['estimated_time_elapsed_genDataset'] = "--:--"
    app_config['completion_percentage_fusim'] = 0
    app_config['estimated_time_elapsed_fusim'] = "--:--"
    cancellation_requested = True


@dataset_generation_blueprint.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Nessun file caricato'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'Nome file non valido'})

    # Processa il file qui (puoi utilizzare le informazioni sul gene come desiderato)

    return jsonify({'success': 'File caricato con successo'})



