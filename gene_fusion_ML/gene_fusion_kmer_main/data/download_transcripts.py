import re
import shutil
import requests
import os
import time

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

# Main function to process each gene, fetch transcripts and their DNA sequences
def process_genes_nonChimeric(gene, directory, filename):

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
            # Save each gene transcript in a FASTQ format
            #filename = f"transcripts/{gene_name}.fastq"
            filename= directory+filename
            # if not os.path.exists(directory):
            #     os.makedirs(directory)
            print(f"Sequences for {gene} saved in FASTQ format.")
            with open(filename, 'w') as file:
                for transcript_id, sequence in transcript_sequences.items():
                    # Format FASTQ entries
                    file.write(f">ref|fusionGene={gene}-{gene}\n")  # FASTQ identifier
                    file.write(f"{sequence}\n")  # DNA sequence

            print(f"Sequences for {gene} saved in FASTQ format.")
    time.sleep(1)  # Pause between genes


# Main function to process each gene, fetch transcripts and their DNA sequences
def process_genes_in_one_file(input_file, output_file):
    gene_list = read_gene_list(input_file)

    with open(output_file, 'a') as fasta_file:  # Open file in append mode
        for gene in gene_list:
            print(f"Processing gene: {gene}")
            transcripts = fetch_transcripts(gene)

            if transcripts:
                for transcript in transcripts:
                    print(f"Fetching sequence for transcript: {transcript}")
                    sequence = fetch_transcript_sequence(transcript)

                    if sequence:
                        # Write transcript and sequence in FASTA format
                        fasta_file.write(f">{transcript}\n{sequence}\n")

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
        pattern = re.compile(r"^[A-Za-z0-9\-]+?\|ENSG\d+\.\d+$")

        # Apri il file di input in modalità lettura
        with open(input_file, 'r') as infile:
            # Leggi tutte le righe
            lines = infile.readlines()

        # Crea una lista per memorizzare i nomi dei geni estratti
        gene_names = []

        # Per ogni linea nel file, separa il nome del gene dall'ENSG se il formato è corretto
        for line in lines:
            line = line.strip()  # Rimuovi eventuali spazi o newline
            if pattern.match(line):  # Verifica se la linea corrisponde al formato
                gene_name = line.split('|')[0]  # Prendi la parte prima del '|'
                gene_names.append(gene_name)
            else:
                print(f"Formato non valido trovato per la conversione: {line}")
                return  # Esce dalla funzione se trova un formato non valido

        # Scrivi i nomi dei geni in un nuovo file di output solo se tutte le linee sono valide
        with open(output_file, 'w') as outfile:
            for gene_name in gene_names:
                outfile.write(f"{gene_name}\n")

        print(f"Conversione completata! File salvato come: {output_file}")

    except Exception as e:
        print(f"Si è verificato un errore: {e}")

def main():
    custom_panel = "custom_panel_19.txt"
    convert_gene_file(custom_panel, custom_panel)
    process_genes_in_one_file(custom_panel)

if __name__ == "__main__":
    main()
