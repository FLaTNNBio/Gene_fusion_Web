# Esegue fusim e nel mentre un thread viene avviato per controllare se l'utente sta annullando il comando
import os
import subprocess
import sys
import threading
import time

from gene_fusion_webApp.datasets_generation.directory_utility import *

cancellation_requested=False

def execute_fusim_script():
    global process, cancellation_requested

    # Imposta la directory di fusim per eseguire fusim
    fusim_directory = move_to_directory_fusim()

    # Percorso di execute.py
    execute_directory = os.path.join(fusim_directory, 'execute.py')

    fusim_user_directory = move_to_user_directory_fusim()

    # Percorso di custom-panel.txt
    custom_panel_directory = os.path.join(fusim_user_directory, 'custom_panel.txt')

    fusim_user_directory = move_to_user_directory_fusim()
    session_key = get_session_key()

    python_executable = sys.executable

    try:
        # Avvia il processo in background
        process = subprocess.Popen([python_executable,
                                    execute_directory, custom_panel_directory, fusim_directory, fusim_user_directory,
                                    session_key])

        # Utilizza un thread per monitorare l'annullamento
        cancellation_thread = threading.Thread(target=check_cancellation)
        cancellation_thread.start()

        # Attendi il termine del processo
        process.wait()
        print('execute.py è stato eseguito con successo.')

        # Comando per il refresh della pagina
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'esecuzione di execute.py: {e}")
    finally:
        # Pulisci il processo alla fine (potrebbe già essere terminato)
        if process:
            process.terminate()
            process = None  # Pulisci la variabile globale


# Un thread controlla questo flag e verifica se sia True o False, se True, killa il comando(subprocess)
def check_cancellation():
    global cancellation_requested

    while not cancellation_requested:
        # Attendi un breve intervallo prima di verificare l'annullamento
        time.sleep(2)

    # Se l'annullamento è stato richiesto, interrompi il processo
    if process:
        cancellation_requested = False
        process.terminate()
