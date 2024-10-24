import os
import shutil

from flask import session

def get_session_key():
    session_key_prefix = session['key'][:12]
    return session_key_prefix


def move_to_directory_fusim():
    # Imposta il percorso della cartella dello script fusim
    main_directory = os.path.join(os.path.dirname(__file__), '../..')

    # Percorso della directory 'fusim' sopra 'main'
    fusim_directory = os.path.join(main_directory, 'fusim')


    if fusim_directory:
        return fusim_directory

    return None


def move_to_user_directory_fusim():
    # Ottenere i primi 10 caratteri dalla chiave di sessione
    session_key_prefix = session['key'][:12]

    # Imposta il percorso della cartella dello script fusim
    main_directory = os.path.join(os.path.dirname(__file__), '../..')

    # Percorso della directory 'fusim' sopra 'main'
    fusim_directory = os.path.join(main_directory, 'fusim')

    user_directory_fusim = os.path.join(fusim_directory, 'users_id', session_key_prefix)

    if user_directory_fusim:
        return user_directory_fusim

    return None


def move_to_directory_Gen_dataset():
    # Imposta il percorso della cartella dello script fusim
    main_directory = os.path.join(os.path.dirname(__file__), '../..')

    # Percorso della directory 'Generazione_dataset' sopra 'main'
    gen_dataset_directory = os.path.join(main_directory, 'fusim/Generazione_dataset')

    if gen_dataset_directory:
        return gen_dataset_directory

    return None


def move_to_user_directory_Gen_dataset():
    # Ottenere i primi 10 caratteri dalla chiave di sessione
    session_key_prefix = session['key'][:12]

    # Imposta il percorso della cartella dello script fusim
    main_directory = os.path.join(os.path.dirname(__file__), '../..')

    # Percorso della directory 'Generazione_dataset' sopra 'main'
    gen_dataset_directory = os.path.join(main_directory, 'fusim/Generazione_dataset')

    user_directory_gen_dataset = os.path.join(gen_dataset_directory, 'users_id', session_key_prefix)

    if user_directory_gen_dataset:
        return user_directory_gen_dataset


def delete_folder(folder_path):
    # Verifica se la cartella esiste
    if os.path.exists(folder_path):
        # Cancella la cartella
        shutil.rmtree(folder_path)
        # print("La cartella è stata cancellata con successo.")
    else:
        print("La cartella specificata non esiste.")

def delete_files_in_directory(directory):
    # Verifica se la directory esiste
    if not os.path.exists(directory):
        print(f"La directory {directory} non esiste.")
        return

    # Elimina tutti i file nella directory
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"File {filename} eliminato.")
        except Exception as e:
            print(f"Errore durante l'eliminazione del file {filename}: {e}")