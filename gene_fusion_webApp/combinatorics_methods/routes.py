import csv
import hashlib
import os
import secrets
import shutil
import signal
import subprocess
import sys
import threading
import zipfile

from flask import render_template, request, jsonify, Blueprint, redirect, url_for, current_app, session, send_file
from pip._internal.utils.misc import ensure_dir
from werkzeug.utils import secure_filename

from gene_fusion_ML.gene_fusion_kmer_main.data.download_transcripts import convert_gene_file, process_genes_in_one_file
from gene_fusion_webApp.combinatorics_methods.input_file_validator import validate_chimeric_format, \
    validate_non_chimeric_format, validate_test_result_format, validate_custom_panel_format

combinatorics_method_blueprint = Blueprint(
    "combinatorics_method",
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
@combinatorics_method_blueprint.before_request
def before_request():
    if 'key' not in session:
        user_ip = request.remote_addr
        session['key'] = generate_session_key(user_ip)


@combinatorics_method_blueprint.route("/combinatorics_method", methods=['GET', 'POST'])
def index():
    # Puoi ora utilizzare session['key'] all'interno di questa rotta
    print("Chiave di sessione:", session['key'])
    user_id = session.get('key')
    return render_template('combinatorics_method.html', user_id=user_id)


# Controlli per la validazione degli input dell'utente
@combinatorics_method_blueprint.route("/validate_files", methods=["POST"])
def validate_files():
    # Ottieni i file dal request
    execution_type = request.form.get("executionType")

    if execution_type == "combinatorics":
        chimeric_combinatorics_file = request.files.get("chimericFileCombinatorics")
        non_chimeric_combinatorics_file = request.files.get("nonChimericFileCombinatorics")
        test_result_file_chimeric = request.files.get("testResultFile1")
        test_result_file_nonChimeric = request.files.get("testResultFile2")

        # Verifica che i file siano presenti e validi
        if not chimeric_combinatorics_file or not non_chimeric_combinatorics_file:
            return jsonify({"success": False, "message": "Both Chimeric and Non-Chimeric datasets are required."})

        if test_result_file_chimeric is None or test_result_file_nonChimeric is None:
            return jsonify({"success": False, "message": "Test result file is required."})

        # Esegui la logica di validazione per i file di Combinatorics

        # Leggi i file
        chimeric_content = chimeric_combinatorics_file.read().decode('utf-8')
        non_chimeric_content = non_chimeric_combinatorics_file.read().decode('utf-8')
        test_result_content_chimeric = test_result_file_chimeric.read().decode(
            'utf-8') if test_result_file_chimeric else None
        test_result_content_nonChimeric = test_result_file_nonChimeric.read().decode(
            'utf-8') if test_result_file_nonChimeric else None

        # Controlla il formato
        is_valid_chimeric_combinatoric = validate_chimeric_format(chimeric_content)
        is_valid_non_chimeric_combinatoric = validate_non_chimeric_format(non_chimeric_content)
        is_valid_test_result_chimeric = validate_test_result_format(
            test_result_content_chimeric) if test_result_content_chimeric else True
        is_valid_test_result_nonChimeric = validate_test_result_format(
            test_result_content_nonChimeric) if test_result_content_nonChimeric else True

        if not is_valid_chimeric_combinatoric:
            return jsonify({"success": False, "message": "Invalid Chimeric dataset format."})

        if not is_valid_non_chimeric_combinatoric:
            return jsonify({"success": False, "message": "Invalid Non-Chimeric dataset format."})

        if not is_valid_test_result_chimeric:
            return jsonify({"success": False, "message": "Invalid Test result Chimeric format"})

        if not is_valid_test_result_nonChimeric:
            return jsonify({"success": False, "message": "Invalid Test result Non-Chimeric format"})

    elif execution_type == "testFusion":
        chimeric_file = request.files.get("chimericFile")
        non_chimeric_file = request.files.get("nonChimericFile")

        if not chimeric_file or not non_chimeric_file:
            return jsonify({"success": False, "message": "Both Chimeric and Non-Chimeric datasets are required."})
        else:
            # Esegui la logica di validazione per i file di Test Fusion
            # Leggi i file
            chimeric_content = chimeric_file.read().decode('utf-8')
            non_chimeric_content = non_chimeric_file.read().decode('utf-8')

            # Controlla il formato
            is_valid_chimeric = validate_chimeric_format(chimeric_content)
            is_valid_non_chimeric = validate_non_chimeric_format(non_chimeric_content)

            if not is_valid_chimeric:
                return jsonify({"success": False, "message": "Invalid Chimeric dataset format."})

            if not is_valid_non_chimeric:
                return jsonify({"success": False, "message": "Invalid Non-Chimeric dataset format."})
    elif execution_type == "trainingCombinatoricsModel":
        custom_panel_file = request.files.get("custom_panelFile")

        custom_panel_content = custom_panel_file.read().decode('utf-8')

        # Controlla il formato
        is_valid_custom_panel = validate_custom_panel_format(custom_panel_content)

        if not is_valid_custom_panel:
            return jsonify({"success": False, "message": "Invalid Custom panel format."})

    return jsonify({"success": True, "message": "Files are valid."})


# Ottiene i valori di fusion score dai file che iniziano per "fusion_" nella directory metrics
def get_fusion_scores():
    metrics_path = 'Combinatorics_ML_Gene_Fusion/testing/test_result/metrics/'

    methods = ['analysis_with_known_genes_check_range_majority', 'analysis_with_known_genes_consecutive_frequency',
               'analysis_with_known_genes_no_check_range_majority']  # Modifica questi nomi in base ai tuoi metodi
    fusion_scores = {}

    for method in methods:
        csv_file_path = os.path.join(metrics_path, f'fusion_accuracy_{method}.csv')

        if os.path.exists(csv_file_path):
            with open(csv_file_path, 'r') as csv_file:
                csv_reader = csv.reader(csv_file)
                next(csv_reader)  # Salta l'intestazione
                for row in csv_reader:
                    fusion_scores[method] = {'name': row[0], 'fusion_score': float(row[1])}
        else:
            fusion_scores[method] = {'name': method, 'fusion_score': None}

    return fusion_scores


# # Funzione di monitoraggio dell'annullamento (dummy per esempio, personalizzala come serve)
# def check_cancellation():
#     # Qui inserisci la logica per verificare se l'operazione è stata annullata
#     pass


def clear_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)  # Rimuove ricorsivamente la directory e tutto il suo contenuto


@combinatorics_method_blueprint.route('/execute_command/<int:command_id>', methods=['POST'])
def execute_command(command_id):
    global cancellation_requested
    process = None

    # Recupera i file caricati e i parametri dal form
    chimeric_file = request.files.get("chimericFile")
    non_chimeric_file = request.files.get("nonChimericFile")
    chimericCombinatorics_file = request.files.get("chimericFileCombinatorics")
    nonChimericCombinatorics_file = request.files.get("nonChimericFileCombinatorics")

    test_result_file1 = request.files.get("testResultFile1")
    test_result_file2 = request.files.get("testResultFile2")

    custom_panelFile = request.files.get("custom_panelFile")

    # Estrai i parametri del range e del passo (threshold per algoritmi combinatori)
    threshold_min = float(request.form['thresholdMin'])
    threshold_max = float(request.form['thresholdMax'])
    threshold_step = str(float(request.form['thresholdStep']))

    threshold_search_range = (threshold_min, threshold_max)
    threshold_search_range_str = f"{threshold_search_range[0]},{threshold_search_range[1]}"

    # Execution directory
    combinatorics_directory = os.path.join(os.getcwd(), 'Combinatorics_ML_Gene_Fusion/')
    testing_execute_directory = os.path.join(combinatorics_directory, 'testing.py')
    fingerprint_execute_directory = os.path.join(combinatorics_directory, 'fingerprint.py')
    training_execute_directory = os.path.join(combinatorics_directory, 'training.py')

    # Training directory
    custom_panel_dir = os.path.join(combinatorics_directory, 'training', 'custom_panel/')
    transcritpts_dir = os.path.join(combinatorics_directory, 'training', 'transcripts/')
    fingerprints_dir = os.path.join(combinatorics_directory, 'training', 'Fingerprints/')
    factorization_fingerprint_dir = os.path.join(combinatorics_directory, 'training', 'Factorizations_fingerprint/')
    dataset_dir = os.path.join(combinatorics_directory, 'training', 'datasets_X_y/')
    model_dir = os.path.join(combinatorics_directory, 'training', 'models/')

    # Testing directory
    chimeric_dir = os.path.join(combinatorics_directory, 'testing', 'chimeric/')
    non_chimeric_dir = os.path.join(combinatorics_directory, 'testing', 'non_chimeric/')
    test_result_dir = os.path.join(combinatorics_directory, 'testing', 'test_result/')

    download_dir = os.path.join(os.getcwd(), 'gene_fusion_webApp', 'static', 'downloads/')

    # Crea le directory se non esistono
    ensure_dir(chimeric_dir)
    ensure_dir(non_chimeric_dir)
    ensure_dir(test_result_dir)

    ensure_dir(transcritpts_dir)
    ensure_dir(custom_panel_dir)
    ensure_dir(fingerprints_dir)
    ensure_dir(factorization_fingerprint_dir)
    ensure_dir(dataset_dir)
    ensure_dir(model_dir)

    clear_directory(chimeric_dir)
    clear_directory(non_chimeric_dir)
    clear_directory(test_result_dir)

    clear_directory(transcritpts_dir)
    clear_directory(custom_panel_dir)
    clear_directory(fingerprints_dir)
    clear_directory(factorization_fingerprint_dir)
    clear_directory(dataset_dir)
    clear_directory(model_dir)

    # Salva i file caricati
    if chimeric_file:
        chimeric_file_path = os.path.join(chimeric_dir, chimeric_file.filename)
        chimeric_file.save(chimeric_file_path)
    if non_chimeric_file:
        non_chimeric_file_path = os.path.join(non_chimeric_dir, non_chimeric_file.filename)
        non_chimeric_file.save(non_chimeric_file_path)
    if chimericCombinatorics_file:
        chimeric_file_path = os.path.join(chimeric_dir, chimericCombinatorics_file.filename)
        chimericCombinatorics_file.save(chimeric_file_path)
    if nonChimericCombinatorics_file:
        non_chimeric_file_path = os.path.join(non_chimeric_dir, nonChimericCombinatorics_file.filename)
        nonChimericCombinatorics_file.save(non_chimeric_file_path)
    if test_result_file1:
        test_result_file_path1 = os.path.join(test_result_dir, test_result_file1.filename)
        test_result_file1.save(test_result_file_path1)
    if test_result_file2:
        test_result_file_path2 = os.path.join(test_result_dir, test_result_file2.filename)
        test_result_file2.save(test_result_file_path2)
    if custom_panelFile:
        custom_panel_file_path = os.path.join(custom_panel_dir, custom_panelFile.filename)
        custom_panelFile.save(custom_panel_file_path)

    try:
        command_args = []
        commands = []
        # Configura i parametri in base al command_id
        if command_id == 1:
            command_args = [
                testing_execute_directory,
                '--step', 'test_fusion',
                '--path', os.path.join(combinatorics_directory, 'testing/'),
                '--path1', chimeric_dir,
                '--path2', non_chimeric_dir,
                '--fasta1', chimeric_file.filename,
                '--fasta2', non_chimeric_file.filename,
                '--best_model', 'RF_CFL_ICFL_COMB-30_K8.pickle',
                '--type_factorization', 'CFL_ICFL_COMB-30', '--k_value', '8',
                '-n', '2',
                '--dictionary', 'yes'
            ]

        elif command_id == 2:
            print("Eseguendo Comando 3: Test Result (Chimeric and Non-Chimeric)")
            command_args = [
                testing_execute_directory,  # Percorso assoluto per 'testing.py'
                '--step', 'test_result',
                '--path1', os.path.join(combinatorics_directory, 'testing/chimeric/'),
                '--path2', os.path.join(combinatorics_directory, 'testing/non_chimeric/'),
                '--testing_path', os.path.join(combinatorics_directory, 'testing/test_result/'),
                '--fasta1', chimericCombinatorics_file.filename,
                '--fasta2', nonChimericCombinatorics_file.filename,
                '--best_model', 'RF_CFL_ICFL_COMB-30_K8.pickle',
                '--type_factorization', 'CFL_ICFL_COMB-30',
                '--k_value', '8',
                '-n', '4',
                '--dictionary', 'yes',
                '--threshold_search_range', threshold_search_range_str,
                '--threshold_search_step', threshold_step
            ]
        elif command_id == 3:
            # Esegui la conversione e processa i geni in un unico file FASTA

            custom_panel = custom_panel_dir + custom_panelFile.filename
            output_file_fasta = transcritpts_dir + 'transcripts_genes.fa'

            # Converte il custom panel e processa i geni, salvandoli in un file fasta
            convert_gene_file(custom_panel, custom_panel)
            process_genes_in_one_file(custom_panel, output_file_fasta)

            # Definizione dei 3 comandi
            commands = [
                # Primo comando: Generare fingerprint dai trascritti genici
                [
                    fingerprint_execute_directory, '--type', '1f_np', '--path', os.path.join(combinatorics_directory, 'training/'), '--fasta',
                    output_file_fasta,  # Passiamo l'output .fasta dal passaggio precedente
                    '--type_factorization', 'CFL_ICFL_COMB-30', '-n', '4', '--dictionary', 'yes'
                ],
                # Secondo comando: Generare dataset_X e dataset_Y dai dati di fingerprint
                [
                    training_execute_directory, '--step', 'dataset', '--path',  os.path.join(combinatorics_directory, 'training/'),
                    '--type_factorization',
                    'CFL_ICFL_COMB-30', '--k_value', '8'
                ],
                # Terzo comando: Addestrare il modello
                [
                    training_execute_directory, '--step', 'train', '--path',  os.path.join(combinatorics_directory, 'training/'),
                    '--type_factorization',
                    'CFL_ICFL_COMB-30', '--k_value', '8', '--model', 'RF', '-n', '4'
                ]
            ]
        # Log di debug
        print(f"Eseguendo comando con command_id={command_id}, args={command_args}")
        stdout, stderr = None, None

        if command_id == 1 or command_id == 2:
            # Esegui il comando
            process = subprocess.Popen(
                [r'C:\Users\eduk4\PycharmProjects\Gene_fusion_Web\venv\Scripts\python.exe'] + command_args,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Attendi il termine del processo
            stdout, stderr = process.communicate()
            print(f"Comando eseguito, stdout={stdout.decode('utf-8')}, stderr={stderr.decode('utf-8')}")

        elif command_id == 3:
            # Eseguire i comandi in sequenza
            for i, command_args in enumerate(commands, 1):
                print(f"Eseguendo comando {i}...")
                # Esegui il comando
                process = subprocess.Popen(
                    [r'C:\Users\eduk4\PycharmProjects\Gene_fusion_Web\venv\Scripts\python.exe'] + command_args,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()

                # Log per debug
                print(f"Comando {i} eseguito, stdout={stdout.decode('utf-8')}, stderr={stderr.decode('utf-8')}")

        if process.returncode == 0 and command_id == 1:
            print(f"Comando eseguito correttamente: {stdout.decode('utf-8')}")

            # Verifica l'estensione corretta per i file di risultato
            chimeric_base_filename = os.path.splitext(chimeric_file.filename)[0]  # Rimuove l'estensione .fastq o .fasta
            non_chimeric_base_filename = os.path.splitext(non_chimeric_file.filename)[0]

            # Percorsi dei risultati generati
            chimeric_result = os.path.join(chimeric_dir,
                                           f'test_fusion_result_CFL_ICFL_COMB-30_K8_{chimeric_base_filename}.txt')
            non_chimeric_result = os.path.join(non_chimeric_dir,
                                               f'test_fusion_result_CFL_ICFL_COMB-30_K8_{non_chimeric_base_filename}.txt')

            # Verifica se i file esistono prima di proseguire
            if not os.path.exists(chimeric_result):
                return jsonify({'success': False, 'error': f'File non trovato: {chimeric_result}'})

            if not os.path.exists(non_chimeric_result):
                return jsonify({'success': False, 'error': f'File non trovato: {non_chimeric_result}'})

            # Crea uno zip con entrambi i file di test result
            zip_filename = os.path.join(download_dir, 'test_result.zip')
            with zipfile.ZipFile(zip_filename, 'w') as test_result_zip:
                test_result_zip.write(chimeric_result, os.path.basename(chimeric_result))
                test_result_zip.write(non_chimeric_result, os.path.basename(non_chimeric_result))

            # Restituisci l'URL del file zip al frontend
            download_url = f'/static/downloads/test_result.zip'
            return jsonify({'success': True, 'download_url': download_url})

        if process.returncode == 0 and command_id == 2:  # Assumendo che si tratti del comando 3
            print(f"Comando eseguito correttamente: {stdout.decode('utf-8')}")

            # Percorso della directory "test_result" da comprimere
            test_result_dir = os.path.join(combinatorics_directory, 'testing', 'test_result')

            # Verifica se la directory di test_result esiste
            if not os.path.exists(test_result_dir):
                return jsonify({'success': False, 'error': f'Directory non trovata: {test_result_dir}'})

            try:
                # Crea uno zip contenente l'intera directory 'test_result'
                zip_filename = os.path.join(download_dir, 'test_result_combinatorics.zip')

                # Comprime la directory 'test_result' in uno zip
                shutil.make_archive(base_name=os.path.splitext(zip_filename)[0],
                                    format='zip',
                                    root_dir=test_result_dir)

                # Restituisci l'URL del file zip al frontend
                download_url = f'/static/downloads/test_result_combinatorics.zip'
                fusion_scores = get_fusion_scores()

                return jsonify({'success': True, 'download_url': download_url, 'fusion_scores': fusion_scores})
            except Exception as e:
                print(f"Errore durante la compressione della directory: {e}")
                return jsonify({'success': False, 'error': str(e)})

        if process.returncode == 0 and command_id == 3:
            print(f"Comando eseguito correttamente: {stdout.decode('utf-8')}")

            # Dopo il terzo comando: Creare uno zip con il modello addestrato
            model_filename = 'RF_CFL_ICFL_COMB-30_K8.pickle'  # Nome del file del modello addestrato
            model_path = os.path.join('training', 'models', model_filename)

            # Verifica che il file del modello esista
            if not os.path.exists(model_path):
                return jsonify({'success': False, 'error': f'Modello non trovato: {model_path}'})

            # Crea uno zip del modello
            zip_filename = os.path.join(download_dir, 'trained_model.zip')
            with zipfile.ZipFile(zip_filename, 'w') as model_zip:
                model_zip.write(model_path, os.path.basename(model_path))

            # Restituisci l'URL del file zip al frontend
            download_url = f'/static/downloads/trained_model.zip'
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


def signal_handler(sig, frame):
    print('Interruzione del programma...')
    # Logica per chiudere risorse se necessario
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
