import re
import shutil
import requests
import os
import time

# A partire da un pannello di geni senza ensg, trova gli ensg  e li inserisce dopo la |
def get_ensg_panel_with_check(gene_panel, species="human"):
    """
    Verifica se gli elementi del pannello di geni sono già nel formato gene|ENSG.
    Se no, associa ciascun gene al suo ENSG ID tramite l'API REST di Ensembl.

    Args:
        gene_panel (list): Lista di geni o gene|ENSG.
        species (str): Specie (default: "human").

    Returns:
        list: Lista di stringhe nel formato gene|ENSG o messaggi di errore.
    """
    server = "https://rest.ensembl.org"
    headers = {"Content-Type": "application/json"}
    results = []

    for entry in gene_panel:
        # Controlla se il formato è già gene|ENSG
        if "|" in entry and entry.split("|")[1].startswith("ENSG"):
            results.append(entry)  # Già nel formato corretto
            continue

        # Altrimenti, tenta di recuperare l'ENSG ID
        gene = entry.split("|")[0]  # Prendi solo il gene
        endpoint = f"/xrefs/symbol/{species}/{gene}?"
        response = requests.get(server + endpoint, headers=headers)

        if response.ok:
            data = response.json()
            if data:
                ensg = data[0]['id']
                results.append(f"{gene}|{ensg}")  # Formatta come gene|ENSG
            else:
                results.append(f"{gene}|No ENSG found")  # Gene non trovato
        else:
            results.append(f"{gene}|Error: {response.status_code}")  # Errore API

    return results


# Function to create the "transcripts" directory if it doesn't exist
def create_transcripts_directory():
    directory = "transcripts"
    if not os.path.exists(directory):
        os.makedirs(directory)

def clear_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)  # Rimuove ricorsivamente la directory e tutto il suo contenuto


# Function to create a FASTQ file for each gene and save its transcript sequences
def save_transcript_sequences(gene_name, transcript_sequences):
    # Create the directory if it doesn't exist
    create_transcripts_directory()

    # Save each gene transcript in a FASTQ format
    filename = f"transcripts/{gene_name}.fastq"
    with open(filename, 'w') as file:
        for transcript_id, sequence in transcript_sequences.items():
            # Format FASTQ entries
            file.write(f">{transcript_id}\n")  # FASTQ identifier
            file.write(f"{sequence}\n")       # DNA sequence


# Function to fetch transcripts for a gene using Ensembl API
def fetch_transcripts(gene_name):
    server = "https://rest.ensembl.org"
    ext = f"/lookup/symbol/homo_sapiens/{gene_name}?expand=1"

    headers = {"Content-Type": "application/json"}
    response = requests.get(server + ext, headers=headers)

    if not response.ok:
        print(f"Error fetching data for gene: {gene_name}")
        return None

    gene_data = response.json()

    if 'Transcript' in gene_data:
        transcripts = [transcript['id'] for transcript in gene_data['Transcript']]
        return transcripts
    else:
        print(f"No transcripts found for gene: {gene_name}")
        return []


# Function to fetch DNA sequence for a transcript
def fetch_transcript_sequence(transcript_id):
    server = "https://rest.ensembl.org"
    ext = f"/sequence/id/{transcript_id}"

    headers = {"Content-Type": "text/plain"}
    response = requests.get(server + ext, headers=headers)

    if not response.ok:
        print(f"Error fetching sequence for transcript: {transcript_id}")
        return None

    return response.text


# Main function to process each gene, fetch transcripts and their DNA sequences
def process_genes(input_file):
    gene_list = read_gene_list(input_file)

    for gene in gene_list:
        print(f"Processing gene: {gene}")
        transcripts = fetch_transcripts(gene)

        if transcripts:
            transcript_sequences = {}
            for transcript in transcripts:
                print(f"Fetching sequence for transcript: {transcript}")
                sequence = fetch_transcript_sequence(transcript)
                if sequence:
                    transcript_sequences[transcript] = sequence
                time.sleep(1)  # Pause to avoid overwhelming the API server

            if transcript_sequences:
                save_transcript_sequences(gene, transcript_sequences)
                print(f"Sequences for {gene} saved in FASTQ format.")
        time.sleep(1)  # Pause between genes



#------------------------------ Funzioni per la generazione dei dati non chimerici nel codice di fusim ----------------------------
def fetch_transcripts_with_metadata(gene_name):
    server = "https://rest.ensembl.org"
    ext = f"/lookup/symbol/homo_sapiens/{gene_name}?expand=1"
    cds_only = True


    # Aggiungi parametri per la richiesta
    params = {"type": "cds"} if cds_only else {}

    headers = {"Content-Type": "application/json"}
    response = requests.get(server + ext, headers=headers, params=params)


    if not response.ok:
        print(f"Error fetching data for gene: {gene_name}")
        return []

    gene_data = response.json()

    if 'Transcript' in gene_data:
        transcripts_metadata = []
        for transcript in gene_data['Transcript']:
            transcript_id = transcript['id']
            metadata = {
                "chromosome": gene_data.get("seq_region_name", "unknown"),  # Cromosoma
                "strand": "+" if gene_data.get("strand", 1) == 1 else "-",  # Filamento
                "exon_indices": ",".join(str(i) for i in range(len(transcript.get('Exon', []))))  # Indici esoni
            }
            transcripts_metadata.append((transcript_id, metadata))
        return transcripts_metadata
    else:
        print(f"No transcripts found for gene: {gene_name}")
        return []


# Main function to process each gene, fetch transcripts and their DNA sequences
def process_genes_nonChimeric(gene, directory, filename, min_length=10, max_length=2500):
    """
    Process a gene, fetch transcripts, and save their sequences in a custom FASTQ-like format.
    Limits the sequence length between min_length and max_length.
    """
    print(f"Processing gene: {gene}")

    # Recupera i trascritti con i loro metadati
    transcripts_with_metadata = fetch_transcripts_with_metadata(gene)

    if transcripts_with_metadata:
        transcript_sequences = {}
        for transcript_data in transcripts_with_metadata:
            transcript_id, metadata = transcript_data  # Separiamo ID e metadati
            print(f"Fetching sequence for transcript: {transcript_id}")
            sequence = fetch_transcript_sequence(transcript_id)

            if sequence:
                # Tronca la sequenza alla lunghezza desiderata
                truncated_sequence = sequence[:max_length]

                # Salva solo le sequenze che soddisfano la lunghezza minima
                if len(truncated_sequence) >= min_length:
                    transcript_sequences[transcript_id] = {
                        "sequence": truncated_sequence,
                        "metadata": metadata
                    }
                else:
                    print(f"Sequence for {transcript_id} is too short after truncation.")
            else:
                print(f"Error fetching sequence for transcript: {transcript_id}")

            time.sleep(1)  # Pause per evitare di sovraccaricare l'API

        if transcript_sequences:
            # Salva ogni trascritto con i metadati in un formato personalizzato
            filename = directory + filename

            with open(filename, 'w') as file:
                for transcript_id, data in transcript_sequences.items():
                    sequence = data["sequence"]
                    metadata = data["metadata"]

                    # Scrivi l'intestazione personalizzata con i metadati
                    file.write(
                        f">ref|{transcript_id}-{transcript_id} "
                        f"fusionGene={gene}-{gene} fusionType=hybrid "
                        f"fusionOptions=auto_correct_orientation,cds_only,symmetrical_exons "
                        f"chrom1={metadata['chromosome']} strand1={metadata['strand']} exonIndex1={metadata['exon_indices']} "
                        f"chrom2={metadata['chromosome']} strand2={metadata['strand']} exonIndex2={metadata['exon_indices']}\n"
                    )
                    file.write(f"{sequence}\n")  # Scrivi la sequenza

            print(f"Sequences for {gene} saved in {filename}.")
        else:
            print(f"No valid transcripts for gene: {gene} (all too short).")
    else:
        print(f"No transcripts metadata retrieved for gene: {gene}")

    time.sleep(1)  # Pause tra i geni
#----------------------------------------------------------------------------------------------------------------------------------

# Main function to process each gene, fetch transcripts and their DNA sequences
def process_genes_in_one_file(input_file, list_ensg, output_file):
    gene_list = read_gene_list(input_file)

    with open(output_file, 'a') as fasta_file:  # Open file in append mode
        for gene, ensg in zip(gene_list, list_ensg):
            print(f"Processing gene: {gene},{ensg}")
            transcripts = fetch_transcripts(gene)

            if transcripts:
                for transcript in transcripts:
                    print(f"Fetching sequence for transcript: {transcript}")
                    sequence = fetch_transcript_sequence(transcript)

                    if sequence:
                        # Write transcript and sequence in FASTA format
                        fasta_file.write(f">{ensg}\n{sequence}\n")

                    time.sleep(1)  # Pause to avoid overwhelming the API server

            time.sleep(1)  # Pause between genes

    print(f"All sequences saved in {output_file}")


# Function to read genes from a file
def read_gene_list(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file.readlines()]

def convert_gene_file(input_file, output_file):
    try:
        # Definisci il pattern che verifica il formato "GENE_NAME|ENSGxxxxxxxxxxx.x"
        pattern_with_dot = re.compile(r"^[A-Za-z0-9\-]+?\|ENSG\d+\.[0-9]+$")
        pattern_without_dot = re.compile(r"^[A-Za-z0-9\-]+?\|ENSG\d+$")

        # Apri il file di input in modalità lettura
        with open(input_file, 'r') as infile:
            # Leggi tutte le righe
            lines = infile.readlines()

        # Crea una lista per memorizzare i nomi dei geni e gli ID ENSG estratti
        gene_names = []
        ensg_ids = []  # Lista per gli ID ENSG

        # Per ogni linea nel file, separa il nome del gene dall'ENSG se il formato è corretto
        for line in lines:
            line = line.strip()  # Rimuovi eventuali spazi o newline
            if pattern_with_dot.match(line) or pattern_without_dot.match(line):  # Verifica se la linea corrisponde al formato
                gene_name = line.split('|')[0]  # Prendi la parte prima del '|'
                ensg_id = line.split('|')[1]  # Prendi la parte dopo il '|', cioè l'ENSG
                gene_names.append(gene_name)
                ensg_ids.append(ensg_id.split('.')[0])  # Aggiungi l'ENSG alla lista
            else:
                print(f"Formato non valido trovato per la conversione: {line}")
                return  # Esce dalla funzione se trova un formato non valido

        # Restituisci la lista degli ID ENSG
        print(f"Lista degli ID ENSG estratti: {ensg_ids}")

        # Scrivi i nomi dei geni in un nuovo file di output solo se tutte le linee sono valide
        with open(output_file, 'w') as outfile:
            for gene_name in gene_names:
                outfile.write(f"{gene_name}\n")

        print(f"Conversione completata! File salvato come: {output_file}")
        return ensg_ids  # Ritorna la lista degli ID ENSG

    except Exception as e:
        print(f"Errore: {e}")

    except Exception as e:
        print(f"Si è verificato un errore: {e}")

def main():
    custom_panel = "genes_panel.txt"
    convert_gene_file(custom_panel, custom_panel)
    process_genes_in_one_file(custom_panel, "genes_panel_transcripts")

if __name__ == "__main__":
    main()