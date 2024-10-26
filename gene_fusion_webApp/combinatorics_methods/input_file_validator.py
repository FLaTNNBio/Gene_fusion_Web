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
    # Espressione regolare per validare ciascuna riga
    pattern = r"^[A-Z0-9]+[|]ENSG\d{11}\.\d+$"

    # Spezza l'input in righe e le processa
    lines = content.strip().split("\n")

    for idx, line in enumerate(lines, 1):
        # Controlla se la riga corrisponde al pattern
        if not re.match(pattern, line):
            return False

    # Se tutte le righe sono valide
    return True
