import csv
import json
import os
import re
import glob


class MetricsCounter:
    def __init__(self):
        self.tp = 0
        self.fp = 0
        self.tn = 0
        self.fn = 0

        self.accuracy = 0
        self.recall = 0
        self.precision = 0
        self.specificity = 0
        self.f1_score = 0

        self.chimeric = 0
        self.non_chimeric = 0

    # Called in positive cases
    def increment_truePositive(self, fusion_gene_1, fusion_gene_2):

        # If 'chimeric' (2 different genes) and there is a fusion, is 'True Positive'
        if fusion_gene_1 != fusion_gene_2:
            self.tp += 1
            self.chimeric += 1

    def increment_falsePositive(self, fusion_gene_1, fusion_gene_2):

        # If 'not chimeric' (2 identical genes) and there is a fusion, is 'False positive'
        if fusion_gene_1 == fusion_gene_2:
            self.fp += 1
            # self.non_chimeric += 1

    def increment_trueNegative(self, fusion_gene_1, fusion_gene_2):

        # if is 'not chimeric' (2 identical genes) and there is not a fusion, is 'True Negative'
        if fusion_gene_1 == fusion_gene_2:
            self.tn += 1
            self.non_chimeric += 1

    def increment_falseNegative(self, fusion_gene_1, fusion_gene_2):

        # if 'chimeric' (2 different genes) and there is not a fusion, is 'False negative'
        if fusion_gene_1 != fusion_gene_2:
            self.fn += 1
            # self.chimeric += 1

    def print_num_chimeric_nonChimeric(self):
        print("CHIMERIC: ", self.chimeric, "\nNON CHIMERIC: ", self.non_chimeric)

    def print_raw_metrics(self):

        print("RAW METRICS: TP: [", self.tp, "] FP: [", self.fp, "] TN: [", self.tn, "] FN: [", self.fn, ']')

    # Calculate metrics for dataset chimeric/nonChimeric
    def calculate_metrics(self):
        # Calculate accuracy
        self.accuracy = (self.tp + self.tn) / (self.tp + self.fp + self.tn + self.fn) if (
                                                                                                 self.tp + self.fp + self.tn + self.fn) != 0 else 0.0

        # Calculate recall
        self.recall = self.tp / (self.tp + self.fn) if (self.tp + self.fn) != 0 else 0.0

        # Calculate precision
        self.precision = self.tp / (self.tp + self.fp) if (self.tp + self.fp) != 0 else 0.0

        # Calculate F1-score
        self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall) if (
                                                                                                       self.precision + self.recall) != 0 else 0.0

        # Calculate specificity
        self.specificity = self.tn / (self.tn + self.fp) if (self.tn + self.fp) != 0 else 0.0

        # Le tue informazioni
        metrics_string = (
            f"Accuracy: {self.accuracy:.2f} | "
            f"Recall: {self.recall:.2f} | "
            f"Precision: {self.precision:.2f} | "
            f"F1-score: {self.f1_score:.2f} | "
            f"Specificity: {self.specificity:.2f}"
        )

        return metrics_string

    def save_csv_metric(self, output_csv_path=None):
        # Save metrics to CSV file if not not None
        if output_csv_path:
            with open(output_csv_path, 'w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(['Metric', 'Value'])
                csv_writer.writerow(['Accuracy', f'{self.accuracy:.2f}'])
                csv_writer.writerow(['Recall', f'{self.recall:.2f}'])
                csv_writer.writerow(['Precision', f'{self.precision:.2f}'])
                csv_writer.writerow(['F1-score', f'{self.f1_score:.2f}'])
                csv_writer.writerow(['Specificity', f'{self.specificity:.2f}'])


# Funzione interna per calcolare il fusion score
def calculate_score(lines, is_chimeric=True):
    count_items = 0
    count_fusion = 0
    count_non_fused = 0

    for line in lines:
        if 'Break Fusion' in line:
            count_items += 1
            if is_chimeric:
                if 'YES' in line:
                    count_fusion += 1
            else:
                # Per file non chimerici, vogliamo contare quanti non sono fusioni
                if 'NO' in line:
                    count_non_fused += 1

    if is_chimeric:
        # Calcola il fusion score per i file chimerici
        fusion_accuracy = (count_fusion * 100) / count_items if count_items != 0 else 0
        print(f'Chimeric Fusion score: {fusion_accuracy:.2f}%')
        return fusion_accuracy
    else:
        # Calcola il non-fusion score per i file non chimerici
        non_fusion_accuracy = (count_non_fused * 100) / count_items if count_items != 0 else 0
        print(f'Non-Chimeric Non-Fusion score: {non_fusion_accuracy:.2f}%')
        return non_fusion_accuracy


def compute_fusion_accuracy(metrics_path, statistical_path1, statistical_path2=None, statistical_name=''):
    """
    Calcola l'accuratezza delle fusioni per file chimerici e non chimerici.

    Se vengono passati due statistical_path, unisce i file di statistiche e calcola
    i fusion score separatamente per file chimerici e non chimerici.
    """

    # Crea il percorso completo per il file CSV
    csv_file_path = os.path.join(metrics_path, f'fusion_accuracy_{statistical_name}.csv')

    # Leggi il primo file statistico (chimerico)
    with open(statistical_path1, 'r') as file1:
        chimeric_lines = file1.readlines()

    # Leggi il secondo file statistico (non chimerico), se fornito
    non_chimeric_lines = []
    if statistical_path2:
        with open(statistical_path2, 'r') as file2:
            non_chimeric_lines = file2.readlines()

    # Calcola il fusion score per file chimerici
    chimeric_fusion_score = calculate_score(chimeric_lines, is_chimeric=True)

    # Calcola il non-fusion score per file non chimerici (se forniti)
    if non_chimeric_lines:
        non_chimeric_fusion_score = calculate_score(non_chimeric_lines, is_chimeric=False)
    else:
        non_chimeric_fusion_score = None

    # Scrivi i risultati nel file CSV
    with open(csv_file_path, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)

        # Scrivi l'intestazione se il file è vuoto
        if csv_file.tell() == 0:
            csv_writer.writerow(['statistics_name', 'Chimeric Fusion Accuracy', 'Non-Chimeric Non-Fusion Accuracy'])

        # Scrivi i dati nel file CSV
        csv_writer.writerow([statistical_name, chimeric_fusion_score, non_chimeric_fusion_score])

    print("Dati scritti con successo nel file CSV.")


# ----------------------------Fusion score metrics from log---------------------------------------------------
def extract_all_metrics_from_log(log_file, optimal_threshold):
    """
    Estrae tutte le metriche da un file di log.
    Restituisce un elenco di dizionari con tutte le metriche trovate.
    """
    # Modelli per estrarre soglie, metriche e parametri
    threshold_pattern = r'Current Threshold: \[(\d+\.\d+)\]'
    metrics_pattern = r'Metrics: TP: (\d+) - FP: (\d+) - TN: (\d+) - FN: (\d+)'
    stats_pattern = r'Accuracy: ([\d.]+) \| Recall: ([\d.]+) \| Precision: ([\d.]+) \| F1-score: ([\d.]+) \| Specificity: ([\d.]+)'

    metrics_list = []  # Lista per raccogliere le metriche estratte

    with open(log_file, 'r') as file:
        log_content = file.read()  # Leggi tutto il contenuto del file

    # Trova tutte le corrispondenze delle soglie nel contenuto del log
    thresholds = re.findall(threshold_pattern, log_content)
    metrics = re.findall(metrics_pattern, log_content)
    stats = re.findall(stats_pattern, log_content)

    optimal_metrics = None

    # Per ciascuna soglia, crea un dizionario delle metriche
    for i in range(len(thresholds)):

        if float(thresholds[i]) == float(optimal_threshold):  # Controlla se la soglia è quella ottimale
            optimal_metrics = {
                'Threshold': float(thresholds[i]),
                'TP': int(metrics[i][0]) if i < len(metrics) else None,
                'FP': int(metrics[i][1]) if i < len(metrics) else None,
                'TN': int(metrics[i][2]) if i < len(metrics) else None,
                'FN': int(metrics[i][3]) if i < len(metrics) else None,
                'Accuracy': float(stats[i][0]) if i < len(stats) else None,
                'Recall': float(stats[i][1]) if i < len(stats) else None,
                'Precision': float(stats[i][2]) if i < len(stats) else None,
                'F1-score': float(stats[i][3]) if i < len(stats) else None,
                'Specificity': float(stats[i][4]) if i < len(stats) else None,
            }
            break  # Esci dal ciclo dopo aver trovato la soglia ottimale

    return optimal_metrics

# def calculate_fusion_score(tp, fp):
#     """
#     Calcola il punteggio di fusione (fusion score).
#     """
#     fusion_accuracy = (tp * 100) / (tp + fp) if (tp + fp) > 0 else 0
#     return fusion_accuracy


def compute_fusion_accuracy_from_logs(testing_path_result, metrics_path, log_file_name, optimal_threshold, statistical_name=''):
    """
    Calcola l'accuratezza delle fusioni da file di log e salva i risultati in un CSV.
    """
    log_file = os.path.join(testing_path_result + "log/", log_file_name)
    # Crea il percorso completo per il file CSV
    csv_file_path = os.path.join(metrics_path, f'fusion_accuracy_{statistical_name}.csv')

    results = []
    optimal_metrics = extract_all_metrics_from_log(log_file, optimal_threshold)
    if optimal_metrics is not None:
        #fusion_score = calculate_fusion_score(tp, fp)
        fusion_score = optimal_metrics['Accuracy'] if optimal_metrics else None

        results.append((statistical_name, fusion_score))
    else:
        results.append((statistical_name, "Data not found for optimal threshold."))

    # Scrivi i risultati nel file CSV
    with open(csv_file_path, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)

        # Scrivi l'intestazione se il file è vuoto
        if csv_file.tell() == 0:
            csv_writer.writerow(['Statistics Name', 'Fusion Accuracy'])

        # Scrivi i dati nel file CSV
        for result in results:
            csv_writer.writerow(result)

    print("Dati scritti con successo nel file CSV.")
