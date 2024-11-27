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


def aggrega_file_fasta_fastq_txt(directory, output_file):
    # Estensioni dei file da aggregare
    valid_extensions = ('.fasta', '.fastq', '.txt')

    # Lista di tutti i file da aggregare
    files_to_merge = []

    # Scorrere la directory per trovare i file con le estensioni desiderate
    for filename in os.listdir(directory):
        if filename.endswith(valid_extensions):
            file_path = os.path.join(directory, filename)
            files_to_merge.append(file_path)

    # Aggiungere il contenuto di tutti i file nell'output
    with open(output_file, 'w') as out_file:
        for file in files_to_merge:
            with open(file, 'r') as f:
                # Scrivere il contenuto del file nell'output
                out_file.write(f.read() + "\n")

    print(f"Tutti i file sono stati aggregati in {output_file}")


# if __name__ == '__main__':
#     # Esempio di utilizzo
#     directory = 'fusim_fasta_dir'  # Inserisci il percorso della tua directory
#     output_file = 'dataset_chimeric_nonChimeric.fasta'  # Nome del file di output
#     aggrega_file_fasta_fastq_txt(directory, output_file)