import shutil
import subprocess
import sys
import threading
import concurrent.futures

from Bio import SeqIO
from Bio.Blast.Applications import NcbiblastnCommandline
import random
import re
import uuid
import os

from fusim.download_transcripts import process_genes_in_one_file, convert_gene_file
# Costruisci il percorso completo al file Blast
# blastn = r"C:/Program Files/NCBI/blast-2.15.0+/bin/blastn"


from progress_bar_utils import *

blast_result_list = []
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ----------------------------------Initializations for progress bar-----------------------------
server_url = "http://127.0.0.1:5000"
session_key = sys.argv[5]
endpoint_url = f"{server_url}/update_completion_percentage_genDataset/"+session_key

# start_time viene memorizzato all'inizio del processo
start_time = datetime.now()

# Numero di elementi completati
completed_items = 0

# Dichiarazione del semaforo per accesso controllato alla variabile completed_items
completed_items_lock = threading.Lock()


# -----------------------------------------------------------------------------------------------


class BlastResult:

    def __init__(self, values):
        self._values = values

    @property
    def qseqid(self):
        return self._values[0] if len(self._values) >= 13 else ""

    @property
    def sseqid(self):
        return self._values[1] if len(self._values) >= 13 else ""

    # Percentage of identical matches
    @property
    def pident(self):
        return float(self._values[2]) if len(self._values) >= 13 else 0

    @property
    def length(self):
        return int(self._values[3]) if len(self._values) >= 13 else 0

    @property
    def nident(self):
        return int(self._values[4]) if len(self._values) >= 13 else 0

    @property
    def qstart(self):
        return int(self._values[5]) if len(self._values) >= 13 else 0

    @property
    def qend(self):
        return int(self._values[6]) if len(self._values) >= 13 else 0

    @property
    def qseq(self):
        return self._values[7] if len(self._values) >= 13 else ""

    @property
    def sstart(self):
        return int(self._values[8]) if len(self._values) >= 13 else 0

    @property
    def send(self):
        return int(self._values[9]) if len(self._values) >= 13 else 0

    @property
    def sseq(self):
        return self._values[10] if len(self._values) >= 13 else ""

    @property
    def gaps(self):
        return self._values[11] if len(self._values) >= 13 else ""

    @property
    def mismatch(self):
        return self._values[12] if len(self._values) >= 13 else ""

    @property
    def sstrand(self):
        return self._values[13] if len(self._values) >= 13 else ""

    @property
    def calculate_error_length(self):
        return self.length - self.nident

    def print_info(self, no_seq=1):

        if self:
            print("\nqseqid:", self.qseqid)
            print("sseqid:", self.sseqid)
            print("pident:", self.pident)
            print("length:", self.length)
            print("nident:", self.nident)
            print("qstart:", self.qstart)
            print("qend:", self.qend)
            print("sstrand ", self.sstrand)

            if no_seq == 1: print("qseq:", self.qseq)

            print("sstart:", self.sstart)
            print("send:", self.send)

            if no_seq == 1: print("sseq:", self.sseq)

            print("gaps:", self.gaps)
            print("mismatch:", self.mismatch)
            print("----------------------")


def generate_random_id():
    uuid_val = str(uuid.uuid4()).replace('-', '')
    formatted_id = f"@{uuid_val[:8]}-{uuid_val[8:12]}-{uuid_val[12:16]}-{uuid_val[16:20]}-{uuid_val[20:]}"
    return formatted_id


# -------------------------------------------------------ESTRAZIONE DATI----------------------------------------------------------------------------------------

def extract_gene_names(file_name):
    # Trova il match della parte del percorso che contiene "fusim_fasta_chimeric/fusion_"
    match1 = re.search(r'fusim_fasta_chimeric\\fusion_', file_name.replace('/', '\\'))
    match2 = re.search(r'fusim_fasta_nonChimeric\\fusion_', file_name.replace('/', '\\'))
    # match2 = re.search(r'fusim_fasta_nonChimeric/fusion_', file_name)

    # Estrai i nomi dei geni dal nome del file
    if match1:
        gene_names = file_name[match1.end():].replace(".fasta", "").split("_")[0:2]
    elif match2:
        gene_names = file_name[match2.end():].replace(".fasta", "").split("_")[0:2]
    else:
        return None

    return gene_names


def read_gene_info_from_file(file_path):
    gene_info_dict = {}
    with open(file_path, "r") as gene_file:
        for line in gene_file:
            gene_name, ensg = line.strip().split("|")
            gene_info_dict[gene_name] = ensg
    return gene_info_dict


def get_ensg_from_gene_name(gene_name, gene_info_dict):
    return gene_info_dict.get(gene_name, "")


def extract_transcript_sequence(transcript_file, ensg_ids):
    # Estrai le sequenze dei trascritti dal file "transcripts_genes.txt"
    transcript_sequences = {}
    with open(transcript_file, "r") as transcript_handle:
        lines = transcript_handle.readlines()
        for line in lines:
            if line.startswith(">"):
                current_ensg_id = line.strip()[1:]
            elif current_ensg_id in ensg_ids:
                # transcript_sequences[current_ensg_id] = line.strip()
                return line.strip()

    # return transcript_sequences
    return None


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------

def replace_file(file_path, old, new):
    # Apri il file in modalità lettura
    with open(file_path, 'r') as file:
        # Leggi il contenuto del file
        content = file.read()

    # Rimuovi tutti i doppi apici dalla stringa
    cleaned_content = content.replace(old, new)

    # Apri il file in modalità scrittura e sovrascrivi il contenuto pulito
    with open(file_path, 'w') as file:
        file.write(cleaned_content)


# -------------------------------------------------------QUERY BLAST E CALCOLO METRICHE--------------------------------------------------------------------------
def run_blast(query_sequence, nameFile, output_file):
    # Comando BLAST
    # //qstart qend sstart send qseq sseq blastn_command_line = NcbiblastnCommandline(cmd='blastn',
    # query=query_sequence, subject=nameFile,outfmt='6 qseqid sseqid pident length nident qstart qend qseq sstart
    # send sseq gaps mismatch sstrand',out=output_file) blastn_command_line_detail = NcbiblastnCommandline(
    # cmd='blastn', query=query_sequence, subject=nameFile, outfmt='0 qseqid sseqid pident length nident',
    # out=output_file_detail)

    # Esegui il comando Blast utilizzando il modulo NcbiblastnCommandline

    blastn_path="C:/Program Files/NCBI/blast-2.16.0+/bin/blastn.exe"

    try:

        blastn_command_line = NcbiblastnCommandline(cmd=blastn_path, query=query_sequence, subject=nameFile,
                                                    outfmt='6 qseqid sseqid pident length nident qstart qend qseq sstart send sseq gaps mismatch sstrand',
                                                    out=output_file)
        output_file, stderr = blastn_command_line()
        output_file_detail = output_file.replace("blast", "blast_detail")

        # blastn_command_line_detail = NcbiblastnCommandline(cmd='blastn', query=query_sequence, subject=nameFile,
        #                                                    outfmt='0 qseqid sseqid pident length nident',
        #                                                    out=output_file_detail)
        # output_file_detail, stderr_detail = blastn_command_line_detail()

        # print('Comando Blast eseguito con successo.')
    except Exception as e:
        print(f'Errore durante l\'esecuzione del comando Blast: {e}')


# Stampa l'intera lista di oggetti BlastResult
def print_blast_result_list(blast_result_list, no_seq=1):
    if blast_result_list:
        for result_values in blast_result_list:
            if result_values:
                result_values.print_info(no_seq)


# Trova i valori minimi e massimi di qstart, qend, sstart e send nella lista di risultati BLAST per geni specifici.
def find_positions_min_max(blast_result_list, ensg_gene):
    if not blast_result_list:
        return None  # Restituisci None se la lista è vuota

    # Inizializza i valori minimi e massimi
    if not blast_result_list[0]:
        return None

    qstart_minimo, qend_massimo = blast_result_list[0].qstart, blast_result_list[0].qend
    sstart_minimo, send_massimo = blast_result_list[0].sstart, blast_result_list[0].send

    # Itera attraverso gli altri risultati e aggiorna i valori se necessario
    for result in blast_result_list:
        if result:
            if result.sseqid == ensg_gene:
                qstart_minimo = min(qstart_minimo, result.qstart)
                qend_massimo = max(qend_massimo, result.qend)
                sstart_minimo = min(sstart_minimo, result.sstart)
                send_massimo = max(send_massimo, result.send)

    return qstart_minimo, qend_massimo, sstart_minimo, send_massimo


def calculate_metrics(blast_results):
    read_identity_list = []
    length_list = []
    error_length_list = []
    query_sequence_startPos = []
    query_sequence_endPos = []

    for result in blast_results:
        # Suddivide il risultato tramite il tab
        result_values = BlastResult(result.split('\t'))
        blast_result_list.append(result_values)

        # Aggiunge i valori alle liste
        read_identity_list.append(result_values.pident)

        length_list.append(result_values.length)
        error_length_list.append(result_values.calculate_error_length)

        query_sequence_startPos.append(result_values.qstart)
        query_sequence_endPos.append(result_values.qend)

    # print_blast_result_list(blast_result_list, 0)

    # Calcola le metriche solo se ci sono risultati
    if read_identity_list:
        total_read_identity = read_identity_list
        total_length = sum(length_list)
        total_error_length = sum(error_length_list)

    else:
        total_read_identity = total_length = total_error_length = 0

    return total_read_identity, total_length, total_error_length


def calculate_metrics_and_print_results(file_name, gene_name_number, gene_names):
    # Lettura dei risultati BLAST dal file
    with open(file_name, "r") as blast_result_file:
        blast_results = blast_result_file.read().strip().split('\n')

    # Check if blast_results is empty
    if not blast_results:
        print("{} - No results found in the file.\n".format(gene_names))
        return [0, 0, 0]

    # Calcolo delle metriche
    total_read_identity, total_length, total_error_length = calculate_metrics(blast_results)
    '''
    # Stampa i risultati
    print("\n--------------------", gene_name_number, "(", gene_names[int(gene_name_number.replace("Gene", "")) - 1],
          ")----------------------------")

    formatted_string1 = "[Read Identity]: {}".format(total_read_identity)
    formatted_string2 = "[gene Length]: {}".format(total_length)
    formatted_string3 = "[Error Length]: {}".format(total_error_length)

    print(f"{timestamp} [INFO] {formatted_string1}")
    print(f"{timestamp} [INFO] {formatted_string2}")
    print(f"{timestamp} [INFO] {formatted_string3}")
    print("----------------------------------------------------------------\n\n")
    '''
    return [total_read_identity, total_length, total_error_length]


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------

# Funzione per creare il file se non esiste
def create_file_if_not_exists(file_path):
    # Crea il file se non esiste
    if not os.path.exists(file_path):
        with open(file_path, 'w'):
            pass  # Questo comando è sufficiente per creare il file vuoto


# Funzione per verificare l'esistenza di un file
def file_exists(file_path):
    return os.path.exists(file_path)


def process_fusion_file(user_directory, input_directory, input_file, output_directory, output_file, gene_info_file,
                        transcript_file, read_identity_threshold, output_gene1_blast, output_gene2_blast):
    # Carica le informazioni sui geni dal file
    gene_info_dict = read_gene_info_from_file(gene_info_file)

    # print("-----------------------------------------------------------------------")
    print(f"{timestamp} [INFO] File input: ", input_file)

    # Estrai i nomi dei geni dal nome del file di input
    gene_names = extract_gene_names(input_file)

    # print(f"{timestamp} [INFO] Fused gene names: ", gene_names)

    # Carica i nomi in formato ENSG dei due geni
    ensg1 = get_ensg_from_gene_name(gene_names[0], gene_info_dict)
    ensg2 = get_ensg_from_gene_name(gene_names[1], gene_info_dict)

    ensg_names = [ensg1, ensg2]

    print(f"{timestamp} [INFO] ENSG gene names: ", ensg_names)

    reference_sequence_gene1 = extract_transcript_sequence(transcript_file, ensg1)
    reference_sequence_gene2 = extract_transcript_sequence(transcript_file, ensg2)

    # Apri il file di output in modalità scrittura
    with open(output_file, "w") as output_handle:
        # Apri il file di input in modalità lettura
        with open(input_file, "r") as input_handle:
            # Leggi le sequenze dal file di input
            for record in SeqIO.parse(input_handle, "fasta"):

                # Genera un identificativo casuale
                id_value = generate_random_id()
                # Estrai le informazioni necessarie dal record
                header_parts = record.description.split(" ")
                header_parts_length = len(header_parts) - 1


                strand_info = header_parts[header_parts_length].split(",")[0].split("=")

                query_fasta = os.path.join(user_directory, 'query.fasta')
                seq1_fasta = os.path.join(user_directory, 'seq1.fasta')
                seq2_fasta = os.path.join(user_directory, 'seq2.fasta')

                create_file_if_not_exists(query_fasta)
                create_file_if_not_exists(seq1_fasta)
                create_file_if_not_exists(seq2_fasta)

                with open(query_fasta, 'w') as file_query_command:
                    file_query_command.write('>{}\n{}'.format(gene_names[0] + "-" + gene_names[1], record.seq))

                file_seq1_command = ""
                with open(seq1_fasta, 'w') as file_seq1_command:
                    file_seq1_command.write('>{}\n{}'.format(ensg1, reference_sequence_gene1))

                file_seq2_command = ""
                with open(seq2_fasta, 'w') as file_seq2_command:
                    file_seq2_command.write('>{}\n{}'.format(ensg2, reference_sequence_gene2))

                run_blast(query_fasta, seq1_fasta, output_gene1_blast)
                run_blast(query_fasta, seq2_fasta, output_gene2_blast)

                results_gene1 = None
                results_gene2 = None

                if file_exists(output_gene1_blast):
                    # Calcola e stampa i risultati per gene1
                    results_gene1 = calculate_metrics_and_print_results(output_gene1_blast, "Gene1", gene_names)
                if file_exists(output_gene1_blast):
                    # Calcola e stampa i risultati per gene2
                    results_gene2 = calculate_metrics_and_print_results(output_gene2_blast, "Gene2", gene_names)

                # Calcola i valori finali di read_identity, total_length e error_free_length
                read_identity = 0

                flag1 = True
                flag2 = True

                if not results_gene1 and not results_gene2:
                    break
                elif not results_gene1:
                    flag1 = False
                elif not results_gene2:
                    flag2 = False

                if isinstance(results_gene1[0], list) and isinstance(results_gene2[0], list):
                    read_identity = (sum(results_gene1[0]) + sum(results_gene2[0])) / (
                            len(results_gene1[0]) + len(results_gene2[0]))

                elif flag1 and isinstance(results_gene1[0], list) and not isinstance(results_gene2[0], list):
                    read_identity = (sum(results_gene1[0])) / (len(results_gene1[0]))

                elif flag2 and not isinstance(results_gene1[0], list) and isinstance(results_gene2[0], list):
                    read_identity = (sum(results_gene2[0])) / (len(results_gene2[0]))

                total_length = len(record.seq)  # gene fused length = (results_gene1[1] + results_gene2[1])

                error_free_length = total_length - (results_gene1[2] + results_gene2[2])
                '''
                print("\n---------------------Gene1 + Gene2 -----------------------------")
                # Stampa le medie
                print(f"{timestamp} [INFO] Final Read Identity: ", read_identity)
                print(f"{timestamp} [INFO] Total Length: ", total_length)
                print(f"{timestamp} [INFO] Error-free_length: ", error_free_length)
                print("----------------------------------------------------------------\n\n")
                '''
                qstart_minimo1, qend_massimo1, sstart_minimo1, send_massimo1 = find_positions_min_max(blast_result_list,
                                                                                                      ensg1)
                qstart_minimo2, qend_massimo2, sstart_minimo2, send_massimo2 = find_positions_min_max(blast_result_list,
                                                                                                      ensg2)

                #print(qstart_minimo1, qend_massimo1, sstart_minimo1, send_massimo1)
                if qstart_minimo1 == None:
                    exit(0)

                if read_identity > read_identity_threshold:
                    # Costruisci la nuova intestazione
                    new_header = f"{id_value} {gene_names[0]}|{ensg1}--{gene_names[1]}|{ensg2},{strand_info[1]}strand,0-{total_length} length={total_length} error-free_length={error_free_length} read_identity={read_identity:.2f}%"

                    # Scrivi il nuovo record nel file di output
                    # output_handle.write(f">{new_header}\n{record.seq}\n")
                    output_handle.write(f"{new_header}\n{record.seq}\n")

                # Svuoto la lista di query blast
                # print("\nLunghezza lista query: ", len(blast_result_list))
                blast_result_list.clear()


# Definisci la funzione che processa ogni singolo file
def process_single_file(user_directory, input_directory, input_file_path, output_directory, output_file,
                        gene_info_file, transcript_file, read_identity_threshold, output_gene1_blast,
                        output_gene2_blast,
                        completed_items_lock, completed_items, endpoint_url, num_files_length, start_time):
    # Esegui il processo per il file corrente
    process_fusion_file(user_directory, input_directory, input_file_path, output_directory, output_file,
                        gene_info_file, transcript_file, read_identity_threshold, output_gene1_blast,
                        output_gene2_blast)

    # Aumenta il contatore degli elementi completati (con un mutex in modo controllato)
    with completed_items_lock:
        completed_items[0] += 1
        # Aggiorna la percentuale e la invia al backend
        update_and_send_percentage(endpoint_url, num_files_length, completed_items[0], start_time,
                                   "completion_percentage_genDataset", "estimated_time_elapsed_genDataset")

def process_directory(user_directory, input_directory, num_files_length, output_directory, gene_info_file, transcript_file,
                      read_identity_threshold, output_gene1_blast,
                      output_gene2_blast):
    global completed_items
    global start_time

    # Assicurati che la cartella di output esista
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Inizializza il contatore degli elementi completati e il lock
    completed_items = [0]
    completed_items_lock = threading.Lock()

    # Creazione del pool di thread
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = []
        # Scorri tutti i file nella cartella di input
        for input_file in os.listdir(input_directory):
            if input_file.endswith(".fasta"):
                input_file_path = os.path.join(input_directory, input_file)

                # Genera il nome del file di output nella cartella di output
                output_file = os.path.join(output_directory, f"output_{input_file}")
                print("DIR: ", input_file_path)

                # Esegui il processo per il file corrente
                # process_fusion_file(user_directory, input_directory, input_file_path, output_directory, output_file,
                #                     gene_info_file,
                #                     transcript_file, read_identity_threshold, output_gene1_blast,
                #                     output_gene2_blast)
                #
                # # Aumenta il contatore degli elementi completati(con un mutex in modo controllato)
                # with completed_items_lock:
                #     completed_items += 1
                #     # Aggiorna la percentuale e la invia al beckend ('/update_completion_percentage_genDataset', methods=['POST'])
                #     update_and_send_percentage(endpoint_url, num_files_length, completed_items, start_time,
                #                                "completion_percentage_genDataset", "estimated_time_elapsed_genDataset")

                # Sottometti l'elaborazione del file al pool di thread
                futures.append(executor.submit(process_single_file, user_directory, input_directory, input_file_path,
                                               output_directory, output_file, gene_info_file, transcript_file,
                                               read_identity_threshold, output_gene1_blast, output_gene2_blast,
                                               completed_items_lock, completed_items, endpoint_url, num_files_length,
                                               start_time))
        # Attendi che tutti i thread completino l'esecuzione
        concurrent.futures.wait(futures)

def move_file(from_dir_file, to_dir_file):
    # Verifica se il file esiste
    if os.path.exists(from_dir_file):
        # Sposta il file nella cartella "uploads"
        shutil.move(from_dir_file, to_dir_file)
        print("Il file è stato spostato con successo nella cartella "+to_dir_file)
    else:
        print("Il file specificato non esiste.")

def delete_folder(folder_path):
    # Verifica se la cartella esiste
    if os.path.exists(folder_path):
        # Cancella la cartella
        shutil.rmtree(folder_path)
        # print("La cartella è stata cancellata con successo.")
    else:
        print("La cartella specificata non esiste.")

def aggregate_files(folder_path, output_prefix, random_number):
    # Lista dei file nella cartella
    files = os.listdir(folder_path)

    # Filtra i file che iniziano per "output_fusion"
    relevant_files = [file for file in files if file.startswith("output_fusion")]


    # Directory
    combinatorics_directory = os.path.join(os.getcwd(), 'Combinatorics_ML_Gene_Fusion/')
    fingerprints_dir = os.path.join(combinatorics_directory, 'training', 'Fingerprints/')
    fingerprint_execute_directory = os.path.join(combinatorics_directory, 'fingerprint.py')
    download_path = "gene_fusion_webApp/static/downloads/"

    # Nome del file di output con numero casuale
    output_filename = f"{output_prefix}_{random_number}.fastq"
    output_file_path = os.path.join(download_path, output_filename)


    # Apri il file di output in modalità scrittura
    with open(output_file_path, 'w') as output_file:
        # Concatena i contenuti di ciascun file nella lista
        for file_name in relevant_files:
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r') as input_file:
                output_file.write(input_file.read())

    command_args = []
    try:
        if output_prefix.__eq__("dataset_chimeric"):
            command_args = [
                fingerprint_execute_directory,
                '--type', 'only_dataset',
                '--path',download_path,
                '--dictionary_path','fusim/',
                '--filenamePath', "fingerprint_"+ output_prefix + "_" +str(random_number)+"_",
                '--fasta',output_file_path,
                '--type_factorization', 'CFL_ICFL_COMB-30',
                '-n', '4',
                '--fact', 'no_create',
                '--dictionary', 'yes'
            ]
        elif output_prefix.__eq__("dataset_nonChimeric"):
            command_args = [
                fingerprint_execute_directory,
                '--type', 'only_dataset',
                '--path',download_path,
                '--dictionary_path', 'fusim/',
                '--filenamePath', "fingerprint_"+ output_prefix+ "_" +str(random_number)+"_",
                '--fasta',output_file_path,
                '--type_factorization', 'CFL_ICFL_COMB-30',
                '-n', '4',
                '--fact', 'no_create',
                '--dictionary', 'yes'
            ]

        # Esegui il comando
        process = subprocess.Popen(
            [r'C:\Users\eduk4\PycharmProjects\Gene_fusion_Web\venv\Scripts\python.exe'] + command_args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Attendi il termine del processo
        stdout, stderr = process.communicate()

        print(f"Comando eseguito, stdout={stdout.decode('utf-8')}, stderr={stderr.decode('utf-8')}")

    except Exception as e:
        print(f"Errore durante l'esecuzione del comando: {e}")


    print(f"Aggregazione completata in {output_file_path}")

    #move_file(output_file_path, 'gene_fusion_webApp/static/downloads')

    update_name_file("http://127.0.0.1:5000/get_name_file",output_filename)




def main_exec():
    # Verifica se è stato fornito un argomento per il nome del file
    if len(sys.argv) != 6:
        print("Usage: python execute.py <input_file>")
        sys.exit(1)

    custom_panel = sys.argv[1]
    generazione_dataset_directory = sys.argv[2]
    user_directory_gen_dataset = sys.argv[3]
    user_directory_fusim = sys.argv[4]


    # Generazione file transcripts_genes.txt partendo dai trascritti passati nel pannello genico
    custom_panel_transcriptGen = "fusim/Generazione_dataset/custom_panel_transcripts.txt"
    # Elimina il file se esiste
    if os.path.exists(custom_panel_transcriptGen):
        os.remove(custom_panel_transcriptGen)
    list_ensg=convert_gene_file(custom_panel, custom_panel_transcriptGen)

    transcript_file = os.path.join(generazione_dataset_directory, "transcripts_genes.txt")
    # Elimina il file se esiste
    if os.path.exists(transcript_file):
        os.remove(transcript_file)

    process_genes_in_one_file(custom_panel_transcriptGen,list_ensg,transcript_file)
    #--------------------------------------------------------------------------------------------

    # Creare la directory dell'utente
    os.makedirs(user_directory_gen_dataset, exist_ok=True)
    os.makedirs(user_directory_fusim, exist_ok=True)

    input_directory_chimeric = os.path.join(user_directory_fusim, "fusim_fasta_chimeric")
    input_directory_nonChimeric = os.path.join(user_directory_fusim, "fusim_fasta_nonChimeric")

    # Utilizza os.listdir() per ottenere la lista dei file nella directory
    files_chimeric = [f for f in os.listdir(input_directory_chimeric) if os.path.isfile(os.path.join(input_directory_chimeric, f))]
    num_files_length_chimeric = len(files_chimeric)

    # Utilizza os.listdir() per ottenere la lista dei file nella directory
    files_nonChimeric = [f for f in os.listdir(input_directory_nonChimeric) if os.path.isfile(os.path.join(input_directory_nonChimeric, f))]
    num_files_length_nonChimeric = len(files_nonChimeric)

    # Numero totale di file da generare per dataset chimerico e non chimerico
    num_files_length = num_files_length_chimeric + num_files_length_nonChimeric

    output_directory_chimeric = os.path.join(user_directory_gen_dataset, "output_fasta_dir_chimeric")
    output_directory_nonChimeric = os.path.join(user_directory_gen_dataset, "output_fasta_dir_nonChimeric")

    # Clean output directory if exists
    if os.path.exists(output_directory_chimeric) and os.path.exists(output_directory_nonChimeric):
        shutil.rmtree(output_directory_chimeric, ignore_errors=True)
        shutil.rmtree(output_directory_nonChimeric, ignore_errors=True)

    # Lista di tutte le directory da creare
    directories_to_create = [
        output_directory_chimeric,
        output_directory_nonChimeric
    ]

    # Creazione delle directory se non esistono
    for directory in directories_to_create:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Creata la directory: {directory}")
        else:
            print(f"La directory esiste già: {directory}")

    read_identity_threshold = 80
    output_gene1_blast = os.path.join(user_directory_gen_dataset, "gene1_out_blast.txt")
    output_gene2_blast = os.path.join(user_directory_gen_dataset, "gene2_out_blast.txt")

    # Genera un numero casuale per evitare sovrascritture
    random_number = random.randint(1, 1000)


    # Chiamata alla funzione per processare la directory chimeric per ottenere il dataset chimeric
    thread_dataset_chimeric = threading.Thread(target=process_directory, args=(
        user_directory_gen_dataset, input_directory_chimeric, num_files_length, output_directory_chimeric, custom_panel,
        transcript_file,
        read_identity_threshold, output_gene1_blast,
        output_gene2_blast))

    # Chiamata alla funzione con un thread per processare la directory nonChimeric per ottenere il dataset nonChimeric
    thread_dataset_nonChimeric = threading.Thread(target=process_directory, args=(
        user_directory_gen_dataset, input_directory_nonChimeric, num_files_length, output_directory_nonChimeric, custom_panel,
        transcript_file,
        read_identity_threshold, output_gene1_blast,
        output_gene2_blast))

    # Parametri per la funzione process_directory
    params_chimeric = (
        user_directory_gen_dataset, input_directory_chimeric, num_files_length, output_directory_chimeric, custom_panel,
        transcript_file, read_identity_threshold, output_gene1_blast, output_gene2_blast
    )

    params_nonChimeric = (
        user_directory_gen_dataset, input_directory_nonChimeric, num_files_length, output_directory_nonChimeric,
        custom_panel,
        transcript_file, read_identity_threshold, output_gene1_blast, output_gene2_blast
    )
    # Creazione del pool di thread
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_chimeric = executor.submit(process_directory, *params_chimeric)
        future_nonChimeric = executor.submit(process_directory, *params_nonChimeric)

        # Attendi che tutti i thread completino l'esecuzione
        concurrent.futures.wait([future_chimeric, future_nonChimeric])

        # Verifica se ci sono eccezioni sollevate durante l'esecuzione delle funzioni
        if future_chimeric.exception():
            print(f"Exception in chimeric thread: {future_chimeric.exception()}")
        if future_nonChimeric.exception():
            print(f"Exception in non-chimeric thread: {future_nonChimeric.exception()}")

    print("All threads have finished execution.")

    # thread_dataset_chimeric.start()
    # thread_dataset_nonChimeric.start()

    # thread_dataset_chimeric.join()
    # thread_dataset_nonChimeric.join()

    # Rimuove l'estensione ".txt" da custom_panel se presente
    custom_panel_name = custom_panel.replace(".txt", "")
    # Nome del file di output con numero casuale
    output_custom_panel_path = f"{custom_panel_name}_{random_number}.txt"

    # Rinomina e sposta
    os.rename(custom_panel, output_custom_panel_path)
    shutil.move(output_custom_panel_path, 'gene_fusion_webApp/static/downloads')
    # Esegui entrambe le funzioni in parallelo e attendi la loro terminazione

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(aggregate_files, output_directory_chimeric, "dataset_chimeric", random_number),
            executor.submit(aggregate_files, output_directory_nonChimeric, "dataset_nonChimeric", random_number)
        ]

        # Attendi il completamento di entrambe
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()  # Raccoglie eventuali eccezioni sollevate
            except Exception as e:
                print(f"An error occurred: {e}")


if __name__ == "__main__":
    main_exec()

# Esempio di utilizzo
# process_fusion_file(input_file="fusion_KRT78_GAS7.fasta",  # ../fusim_fasta_dir/
#                     output_file="output.fasta",
#                     gene_info_file="selected-genes",
#                     transcript_file="transcripts_genes.txt",
#                     output_gene1_blast="gene1_out_blast.txt",
#                     output_gene2_blast="gene2_out_blast.txt"
#                     )
