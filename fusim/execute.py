import os
import shutil
import sys
import subprocess
import threading
import concurrent.futures
from itertools import product
from datetime import datetime

# Definisci l'URL del tuo server Flask
from itertools import combinations

from gene_fusion_ML.gene_fusion_kmer_main.data.download_transcripts import process_genes, process_genes_nonChimeric
from progress_bar_utils import update_and_send_percentage

# ----------------------------------Initializations for progress bar-----------------------------
server_url = "http://127.0.0.1:5000"
session_key = sys.argv[4]
endpoint_url = f"{server_url}/update_completion_percentage_fusim/" + session_key

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# start_time viene memorizzato all'inizio del processo
start_time = datetime.now()

# Numero di elementi completati
completed_items = 0

# Dichiarazione del semaforo per accesso controllato alla variabile completed_items
completed_items_lock = threading.Lock()


# -----------------------------------------------------------------------------------------------

# Generate 'chimeric-nonChimeric' fusion
def generate_chimeric_nonChimeric_fusion(fusim_absolute_path, user_directory, genes_panel, num_files_length):
    global completed_items
    global start_time

    saved_genes_chimeric = []  # Inizializza la lista dei geni salvati chimeric
    saved_genes_nonChimeric = []  # Inizializza la lista dei geni salvati non chimeric

    for gene1 in genes_panel:
        for gene2 in genes_panel:

            # Controlla se la fusione deve essere chimerica o non chimerica
            is_chimeric = gene1 != gene2

            command = [
                'java', '-jar', fusim_absolute_path + '/fusim.jar',
                '--gene-model', fusim_absolute_path + '/refFlat.txt',
                '--fusions', '10',
                '--reference', fusim_absolute_path + '/hg19.fa',
                '--fasta-output',
                                user_directory + f'./fusim_fasta_{"chimeric" if is_chimeric else "nonChimeric"}/fusion_{gene1}_{gene2}.fasta',
                '--text-output',
                                user_directory + f'./fusim_txt_{"chimeric" if is_chimeric else "nonChimeric"}/fusion_{gene1}_{gene2}.txt',
                '-1', gene1,
                '-2', gene2,
                '--cds-only',
                '--auto-correct-orientation'
            ]

            # CHIMERIC
            if is_chimeric:
                # Incrementa il contatore ad ogni elemento completato

                # Verifica se i geni sono già stati salvati in ordine inverso
                already_saved_chimeric = False
                for saved_gene1, saved_gene2 in saved_genes_chimeric:
                    if (gene1 == saved_gene2 and gene2 == saved_gene1):
                        already_saved_chimeric = True
                        break

                # Esegui il comando solo se i geni non sono già stati salvati in ordine inverso
                if not already_saved_chimeric:
                    # Esegui il comando
                    subprocess.run(command)

                    # Aggiungi i geni alla lista dei geni salvati
                    saved_genes_chimeric.append((gene1, gene2))

            # NON CHIMERIC
            if not is_chimeric:
                # Verifica se i geni sono già stati salvati in ordine inverso
                already_saved_nonChimeric = False
                for saved_gene1, saved_gene2 in saved_genes_nonChimeric:
                    if (gene1 == saved_gene2 and gene2 == saved_gene1):
                        already_saved_nonChimeric = True
                        break

                # Esegui il comando solo se i geni non sono già stati salvati in ordine inverso
                if not already_saved_nonChimeric:
                    # Esegui il comando
                    #subprocess.run(command)
                    process_genes_nonChimeric(gene1, user_directory + './fusim_fasta_nonChimeric/',
                                              f'/fusion_{gene1}_{gene2}.fasta')
                    process_genes_nonChimeric(gene1, user_directory + './fusim_txt_nonChimeric/',
                                              f'/fusion_{gene1}_{gene2}.txt')
                    # Aggiungi i geni alla lista dei geni salvati
                    saved_genes_nonChimeric.append((gene1, gene2))

            # Aumenta il contatore degli elementi completati(con un mutex in modo controllato)
            with completed_items_lock:
                completed_items += 1

                # Aggiorna la percentuale e la invia al beckend ('/update_completion_percentage', methods=['POST'])
                update_and_send_percentage(endpoint_url, num_files_length, completed_items, start_time,
                                           "completion_percentage_fusim", "estimated_time_elapsed_fusim")


# Funzione per generare fusioni chimeriche in modo concorrente
def generate_chimeric_nonChimeric_fusion_concurrent(fusim_absolute_path, user_directory, genes_panel, num_files_length):
    thread_chimeric_nonChimeric = threading.Thread(target=generate_chimeric_nonChimeric_fusion,
                                                   args=(fusim_absolute_path, genes_panel, num_files_length,))
    thread_chimeric_nonChimeric.start()
    return thread_chimeric_nonChimeric


''' 
generate_chimeric_nonChimeric_fusion_concurrent (MULTITHREAD)

def generate_chimeric_nonChimeric_fusion_concurrent(fusim_absolute_path, genes_panel, num_files_length):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Lista delle coppie di geni
        gene_pairs = list(product(genes_panel, repeat=2))

        # Avvia i processi per tutte le coppie di geni
        futures = [executor.submit(generate_fusion_chimeric_nonChimeric, fusim_absolute_path, gene1, gene2, num_files_length) for gene1, gene2 in gene_pairs]

        # Attendi che tutti i processi abbiano completato l'esecuzione
        concurrent.futures.wait(futures)

def generate_fusion_chimeric_nonChimeric(fusim_absolute_path, gene1, gene2, num_files_length):

    global completed_items
    global start_time

    saved_genes_chimeric = []  # Inizializza la lista dei geni salvati chimeric
    saved_genes_nonChimeric = []  # Inizializza la lista dei geni salvati non chimeric

    # Controlla se la fusione deve essere chimerica o non chimerica
    is_chimeric = gene1 != gene2


    command = [
        'java', '-jar', fusim_absolute_path + '/fusim.jar',
        '--gene-model', fusim_absolute_path + '/refFlat.txt',
        '--fusions', '10',
        '--reference', fusim_absolute_path + '/hg19.fa',
        '--fasta-output',
                        fusim_absolute_path + f'./fusim_fasta_{"chimeric" if is_chimeric else "nonChimeric"}/fusion_{gene1}_{gene2}.fasta',
        '--text-output',
                        fusim_absolute_path + f'./fusim_txt_{"chimeric" if is_chimeric else "nonChimeric"}/fusion_{gene1}_{gene2}.txt',
        '-1', gene1,
        '-2', gene2,
        '--cds-only',
        '--auto-correct-orientation'
    ]

    # CHIMERIC
    if is_chimeric:
        # Incrementa il contatore ad ogni elemento completato

        # Verifica se i geni sono già stati salvati in ordine inverso
        already_saved_chimeric = False
        for saved_gene1, saved_gene2 in saved_genes_chimeric:
            if (gene1 == saved_gene2 and gene2 == saved_gene1):
                already_saved_chimeric = True
                break

        # Esegui il comando solo se i geni non sono già stati salvati in ordine inverso
        if not already_saved_chimeric:
            # Esegui il comando
            subprocess.run(command)

            # Aggiungi i geni alla lista dei geni salvati
            saved_genes_chimeric.append((gene1, gene2))

    # NON CHIMERIC
    if not is_chimeric:

        # Verifica se i geni sono già stati salvati in ordine inverso
        already_saved_nonChimeric = False
        for saved_gene1, saved_gene2 in saved_genes_nonChimeric:
            if (gene1 == saved_gene2 and gene2 == saved_gene1):
                already_saved_nonChimeric = True
                break

        # Esegui il comando solo se i geni non sono già stati salvati in ordine inverso
        if not already_saved_nonChimeric:
            # Esegui il comando
            subprocess.run(command)

            # Aggiungi i geni alla lista dei geni salvati
            saved_genes_nonChimeric.append((gene1, gene2))

    # Aumenta il contatore degli elementi completati(con un mutex in modo controllato)
    with completed_items_lock:
        completed_items += 1

        # Aggiorna la percentuale e la invia al beckend ('/update_completion_percentage', methods=['POST'])
        update_and_send_percentage(endpoint_url, num_files_length, completed_items, start_time)
'''


def create_folder(folder_path):
    if not os.path.exists(folder_path):
        try:
            os.makedirs(folder_path)
            print(f"Cartella creata con successo: {folder_path}")
        except OSError as e:
            print(f"Errore nella creazione della cartella: {e}")
    else:
        print(f"La cartella '{folder_path}' esiste già.")


def main_exec():
    # Verifica se è stato fornito un argomento per il nome del file
    if len(sys.argv) != 5:
        print("Usage: python execute.py <input_file>")
        sys.exit(1)

    custom_panel = sys.argv[1]

    fusim_directory = sys.argv[2]
    user_directory = sys.argv[3]

    # Creare la directory dell'utente
    os.makedirs(user_directory, exist_ok=True)

    # Svuota le cartelle fusim_fasta_dir_chimeric/nonChimeric e fusim_txt_dir_chimeric/nonChimeric
    fasta_dir_chimeric = os.path.join(user_directory, 'fusim_fasta_chimeric')
    txt_dir_chimeric = os.path.join(user_directory, 'fusim_txt_chimeric')
    fasta_dir_nonChimeric = os.path.join(user_directory, 'fusim_fasta_nonChimeric')
    txt_dir_nonChimeric = os.path.join(user_directory, 'fusim_txt_nonChimeric')

    # Rimuovi il contenuto delle cartelle
    shutil.rmtree(fasta_dir_chimeric, ignore_errors=True)
    shutil.rmtree(txt_dir_chimeric, ignore_errors=True)
    shutil.rmtree(fasta_dir_nonChimeric, ignore_errors=True)
    shutil.rmtree(txt_dir_nonChimeric, ignore_errors=True)

    # Chiamate alla funzione per creare le quattro cartelle
    create_folder(fasta_dir_chimeric)
    create_folder(txt_dir_chimeric)
    create_folder(fasta_dir_nonChimeric)
    create_folder(txt_dir_nonChimeric)

    # Leggi i geni dal file custom_panel
    with open(custom_panel, 'r') as file:
        lines = file.readlines()

    # Estrai i nomi dei geni
    # genes = [line.split()[0][1:] for line in lines if line.startswith('>')]

    # Estrai i nomi dei geni
    genes = [line.split("|")[0] for line in lines]

    num_genes = len(lines)

    # Scegli un numero specifico di geni
    genes_panel = genes[:num_genes]  # Sostituisci con i valori effettivi del tuo pannello di geni

    # Filtra solo le coppie di geni uguali es:(GBA3-GBA3) e crea una lista
    equal_gene_pairs = [(gene, gene) for gene in genes_panel]
    print(equal_gene_pairs)

    num_files_length = len(genes_panel)

    # Avvia fusim in Multithread
    # thread_chimeric_nonChimeric = generate_chimeric_nonChimeric_fusion_concurrent(fusim_directory, genes_panel, num_files_length)

    generate_chimeric_nonChimeric_fusion(fusim_directory, user_directory, genes_panel, num_files_length)


if __name__ == "__main__":
    main_exec()
