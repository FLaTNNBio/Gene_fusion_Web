import csv
import json
import os


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


def compute_fusion_accuracy(metrics_path, statistical_path1, statistical_path2=None, statistical_name=''):
    """
    Calcola l'accuratezza delle fusioni. Se vengono passati due statistical_path,
    unisce i file di statistiche e calcola il fusion score usando le linee unite.
    """

    # Crea il percorso completo per il file CSV
    csv_file_path = os.path.join(metrics_path, f'fusion_accuracy_{statistical_name}.csv')

    # Se statistical_path2 è presente, combina i due file di statistiche
    if statistical_path2:
        with open(statistical_path1, 'r') as file1, open(statistical_path2, 'r') as file2:
            merged_lines = file1.readlines() + file2.readlines()
    else:
        # Usa solo il primo file di statistiche se statistical_path2 non è fornito
        with open(statistical_path1, 'r') as file1:
            merged_lines = file1.readlines()

    count_items = 0
    count_fusion = 0

    # Conta le occorrenze di "Break Fusion" e "YES"
    for line in merged_lines:
        if 'Break Fusion' in line:
            count_items += 1
            if 'YES' in line:
                count_fusion += 1

    # Calcola l'accuratezza delle fusioni
    fusion_accuracy = (count_fusion * 100) / count_items if count_items != 0 else 0
    print(f'Fusion score: {fusion_accuracy:.2f}%')

    # Scrivi i risultati nel file CSV
    with open(csv_file_path, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)

        # Scrivi l'intestazione se il file è vuoto
        if csv_file.tell() == 0:
            csv_writer.writerow(['statistics_name', 'Accuracy'])

        # Scrivi i dati solo con il nome del metodo (statistical_name)
        csv_writer.writerow([statistical_name, fusion_accuracy])

    print("Dati scritti con successo nel file CSV.")


