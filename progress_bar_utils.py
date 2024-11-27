import requests
from datetime import datetime



def get_completion_percentage(total_items, completed_items):
    """
    Calcola la percentuale di completamento.

    Parameters:
    - total_items (int): Numero totale di elementi
    - completed_items (int): Numero di elementi completati

    Returns:
    int: Percentuale di completamento
    """

    if total_items == 0:
        return 0  # Se non ci sono elementi, considera il completamento allo 0%

    completion_percentage = int((completed_items / total_items) * 100)

    # Se il completamento è al 100%, forza la percentuale al 100%
    if completion_percentage == 100:
        return 100

    return completion_percentage


def update_and_send_percentage(endpoint_url, genes_panel_length, completed_items, start_time, completiom_percentage_name,estimated_time_name):
    """
    Aggiorna la percentuale di completamento e invia al server.

    Parameters:
    - endpoint_url (str): endpoint del server (server url + address) example http://localhost:5000 + /home
    - completion_percentage (int): Percentuale di completamento
    -
    """
    # Calcola la percentuale di completamento
    if completiom_percentage_name == "completion_percentage_genDataset":
        completion_percentage = get_completion_percentage(genes_panel_length, completed_items) # (len(genes_panel.txt) ** 2, completed_items)
    else:
        completion_percentage = get_completion_percentage(genes_panel_length** 2, completed_items) # (len(genes_panel.txt) ** 2, completed_items)


    # Calcola il tempo stimato per terminare
    estimated_time_elapsed_raw = str(get_estimated_time_elapsed(start_time, completion_percentage))

    # print(f'Percentuale di completamento: {completion_percentage}%')

    estimated_time_elapsed_second = convert_string_to_seconds(estimated_time_elapsed_raw)

    estimated_time_elapsed = format_time(estimated_time_elapsed_second)
    headers = {'Content-Type': 'application/json'}

    # Dati da inviare al server
    payload = {completiom_percentage_name: completion_percentage,estimated_time_name: estimated_time_elapsed}

    # Invia la richiesta
    try:

        print(f"Payload inviato: {payload}")
        response = requests.post(endpoint_url, json=payload, headers=headers)
        response.raise_for_status()
        print("Percentuale di completamento inviata con successo al server.")
    except requests.exceptions.RequestException as e:
        print(f"Errore durante l'invio della percentuale di completamento al server: {e}")

def update_name_file(endpoint_url, name_file_path):
    headers = {'Content-Type': 'application/json'}
    name_file = "name_file"
    payload = {name_file:name_file_path}
    print(name_file_path)
    # Invia la richiesta
    try:
        print(f"Payload inviato: {payload}")
        response = requests.post(endpoint_url, json=payload, headers=headers)
        response.raise_for_status()
        print("Percentuale di completamento inviata con successo al server.")
    except requests.exceptions.RequestException as e:
        print(f"Errore durante l'invio della percentuale di completamento al server: {e}")

def get_estimated_time_elapsed(start_time, completion_percentage):
    """
    Ottieni il tempo stimato di completamento.

    Parameters:
    - start_time (datetime): Data e ora di inizio
    - completion_percentage (int): Percentuale di completamento

    Returns:
    timedelta: Tempo stimato rimanente
    """
    current_time = datetime.now()
    time_elapsed = current_time - start_time

    # Evita la divisione per zero
    if completion_percentage == 0:
        completion_percentage = 1

    # Calcola il tempo stimato
    estimated_time_elapsed = time_elapsed / completion_percentage * (100 - completion_percentage)

    return estimated_time_elapsed


def format_time(seconds):
    # Calculate the number of days, hours, minutes, and seconds
    days, seconds = divmod(seconds, 86400)  # 86400 seconds in a day
    hours, seconds = divmod(seconds, 3600)  # 3600 seconds in an hour
    minutes, seconds = divmod(seconds, 60)  # 60 seconds in a minute

    # Calculate the number of years, months, and weeks
    years = days // 365
    months = (days % 365) // 30  # Assumes an average month of 30 days
    weeks = (days % 365) % 30 // 7

    # Build the formatted string
    formatted_time = []
    if years > 0:
        formatted_time.append(f"{int(years)} years")
    if months > 0:
        formatted_time.append(f"{int(months)} months")
    if weeks > 0:
        formatted_time.append(f"{int(weeks)} weeks")
    if days > 0:
        formatted_time.append(f"{int(days)} days")
    if hours > 0:
        formatted_time.append(f"{int(hours)} hours")
    if minutes > 0:
        formatted_time.append(f"{int(minutes)} minutes")
    if seconds > 0:
        formatted_time.append(f"{int(seconds)} seconds")

    # Join the formatted parts into a string
    result = ", ".join(formatted_time)

    return result

def convert_string_to_seconds(time_str):
    try:
        # Use '%H:%M:%S.%f' to handle milliseconds
        time_obj = datetime.strptime(time_str, '%H:%M:%S.%f')
        seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second + time_obj.microsecond / 1e6
        return seconds
    except ValueError as e:
        # In case of error, return 0
        print(f"Error during conversion of the string to seconds: {e}")
        return 0