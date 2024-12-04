import re

def validate_chimeric_format(dataset_line):
    # Modificato per ignorare l'ID iniziale e catturare solo i geni
    match = re.match(r'@.+?\s(.+?)--(.+?),', dataset_line)

    if match:
        gene1 = match.group(1).strip()  # Estrai il primo gene
        gene2 = match.group(2).strip()  # Estrai il secondo gene

        # Controllo che i geni siano identici
        if gene1 != gene2:
            print(f"Validazione riuscita")
            return True
        else:
            print(f"Errore: i geni corrispondono. Gene 1: {gene1}, Gene 2: {gene2}")
            return False
    else:
        print("Errore nel formato del dataset non chimeric.")
        return False


def validate_non_chimeric_format(dataset_line):
    # Modificato per ignorare l'ID iniziale e catturare solo i geni
    match = re.match(r'@.+?\s(.+?)--(.+?),', dataset_line)

    if match:
        gene1 = match.group(1).strip()  # Estrai il primo gene
        gene2 = match.group(2).strip()  # Estrai il secondo gene

        # Controllo che i geni siano identici
        if gene1 == gene2:
            print(f"Validazione riuscita")
            return True
        else:
            print(f"Errore: i geni non corrispondono. Gene 1: {gene1}, Gene 2: {gene2}")
            return False
    else:
        print("Errore nel formato del dataset non chimeric.")
        return False

def validate_chimeric_fingerprint_format(dataset_line):
    # Modifica per gestire il formato chimerico: Gene1|ID1--Gene2|ID2
    #match = re.match(r'([A-Za-z0-9|]+)--([A-Za-z0-9|]+)\s(\d.*)', dataset_line)
    pattern = re.compile(
        r"^[A-Za-z0-9\-]+?\|ENSG\d+(\.\d+)?--[A-Za-z0-9\-]+?\|ENSG\d+(\.\d+)?,[+-]STRAND,\d+-\d+\s+\|\s+\d+\s+\|\s+((\d+\s+)*\d+)\s+\|\s+((\d+\s+)*\d+)\s+\|\s+((\d+\s+)*\d+)\s+\|\s+((\d+\s+)*\d+)$"
    )    # Performing the match
    match = pattern.match(dataset_line)

    if match:
        gene1 = match.group(1).strip()  # Estrai il primo gene (con l'ID)
        gene2 = match.group(2).strip()  # Estrai il secondo gene (con l'ID)
        #sequence = match.group(3).strip()  # Estrai la sequenza numerica

        # Controllo che i due geni siano diversi (tipico per i dati chimerici)
        if gene1 != gene2:
            print(f"Validazione riuscita per chimeric: {gene1} -- {gene2}")
            return True
        else:
            print(f"Errore: i geni sono uguali. Gene 1: {gene1}, Gene 2: {gene2}")
            return False
    else:
        print("Errore nel formato del dataset chimeric.")
        return False

def validate_non_chimeric_fingerprint_format(dataset_line):
    # Modifica per gestire il formato non chimerico: Gene|ID--Gene|ID
    match = re.match(r'([A-Za-z0-9|]+)--([A-Za-z0-9|]+)\s(\d.*)', dataset_line)


    if match:
        gene1 = match.group(1).strip()  # Estrai il primo gene (con l'ID)
        gene2 = match.group(2).strip()  # Estrai il secondo gene (con l'ID)
        #sequence = match.group(3).strip()  # Estrai la sequenza numerica

        # Controllo che i due geni siano identici (tipico per i dati non chimerici)
        if gene1 == gene2:
            print(f"Validazione riuscita per non chimeric: {gene1} -- {gene2}")
            return True
        else:
            print(f"Errore: i geni non sono uguali. Gene 1: {gene1}, Gene 2: {gene2}")
            return False
    else:
        print("Errore nel formato del dataset non chimeric.")
        return False
def validate_test_result_format(content):
    """
    Verifica che il formato del test result sia corretto.
    Può contenere più fingerprint separati da '|'.
    """
    lines = content.splitlines()
    for line in lines:
        if line.startswith("FINGERPRINT:"):
            fingerprints = line.split('|')
            if len(fingerprints) < 2:
                return False  # Deve esserci almeno un '|' e più fingerprint
    return True

def validate_custom_panel_format(content):
    """
       Verifica che il formato del custom panel sia corretto.
    """
    # Definisci il pattern che verifica il formato "GENE_NAME|ENSGxxxxxxxxxxx.x"
    pattern_with_dot = re.compile(r"^[A-Za-z0-9\-]+?\|ENSG\d+\.[0-9]+$")
    pattern_without_dot = re.compile(r"^[A-Za-z0-9\-]+?\|ENSG\d+$")

    # Spezza l'input in righe e le processa
    lines = content.strip().split("\n")

    for idx, line in enumerate(lines, 1):
        # Controlla se la riga corrisponde al pattern
        if not re.match(pattern_with_dot, line) and not re.match(pattern_without_dot, line):
            return False

    # Se tutte le righe sono valide
    return True
