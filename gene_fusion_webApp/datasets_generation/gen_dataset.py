import subprocess
import sys
import threading

from gene_fusion_webApp.datasets_generation.directory_utility import *
from gene_fusion_webApp.datasets_generation.fusim import check_cancellation


def execute_gen_dataset_script():
    global process, cancellation_requested
    # Imposta la directory di Generazione_dataset per eseguire lo script di generazione dataset dai dati di fusim
    generazione_dataset_directory = move_to_directory_Gen_dataset()

    execute_directory = os.path.join(generazione_dataset_directory, 'generazione_dataset.py')

    # Directory dell'utente per generazione dataset e fusim
    generazione_dataset_user_directory = move_to_user_directory_Gen_dataset()

    fusim_user_directory = move_to_user_directory_fusim()

    # Percorso di custom-panel.txt
    custom_panel_directory = os.path.join(generazione_dataset_user_directory, 'custom_panel.txt')

    generazione_dataset_directory = move_to_directory_Gen_dataset()
    session_key = get_session_key()
    python_executable = sys.executable

    try:
        # Avvia il processo in background
        process = subprocess.Popen([python_executable,
                                    execute_directory, custom_panel_directory, generazione_dataset_directory,
                                    generazione_dataset_user_directory, fusim_user_directory, session_key])

        # Utilizza un thread per monitorare l'annullamento
        cancellation_thread = threading.Thread(target=check_cancellation)
        cancellation_thread.start()

        # Attendi il termine del processo
        process.wait()
        delete_folder(fusim_user_directory)
        delete_folder(generazione_dataset_user_directory)
        print('Generazione_dataset.py è stato eseguito con successo.')

        # Comando per il refresh della pagina
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'esecuzione di execute.py: {e}")
    finally:
        # Pulisci il processo alla fine (potrebbe già essere terminato)
        if process:
            process.terminate()
            process = None  # Pulisci la variabile globale