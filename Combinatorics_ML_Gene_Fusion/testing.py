import argparse
import logging
import os
import pickle


from functools import partial
from multiprocessing.pool import Pool

from fingerprint_utils import extract_reads_mp, compute_split_fingerprint_by_list
from machine_learning_utils import test_reads_fusion
from factorizations import CFL, ICFL_recursive, CFL_icfl
from factorizations_comb import d_cfl, d_icfl, d_cfl_icfl

from Combinatorics_ML_Gene_Fusion.combinatorics_algorithm import \
    statistical_analysis_with_known_genes_check_range_majority, \
    statistical_analysis_with_known_genes_no_check_range_majority, \
    statistical_analysis_with_known_genes_consecutive_frequency
from Combinatorics_ML_Gene_Fusion.combinatorics_metrics import MetricsCounter, compute_fusion_accuracy, \
    compute_fusion_accuracy_from_logs
import csv

global dataset_name_fastq


def ensure_dir(directory_path):
    """
    Crea una directory se non esiste già.

    :param directory_path: Il percorso della directory da creare
    """
    try:
        # Crea la directory e tutte le sue sottodirectory se non esiste
        os.makedirs(directory_path, exist_ok=True)
        print(f"Directory '{directory_path}' creata o già esistente.")
    except Exception as e:
        print(f"Errore durante la creazione della directory: {e}")


# Given a set of reads, performs classification by using the majority (or thresholds) criterion on best k-finger classification
# args.step = 'test_fusion' ##########################################################################################
def testing_reads_fusion_mp_step(args, dataset_path, dataset_name_fasta):
    input_fasta = dataset_path + dataset_name_fasta
    increment = 2  # 4 if: @43eccc5e-69fb-403d-a19a-99c10b87f829..\nATGAAGATT..\n+\n/&*#'*//,///...
    print(args.n)
    # Apre il file FASTA specificato in input_fasta e legge le linee del file
    print(input_fasta)
    file = open(input_fasta)
    lines = file.readlines()

    # Le linee lette dal file sono divise in parti, dove ogni parte contiene 'increment' linee.
    splitted_read_lines = [lines[i:i + increment] for i in range(0, len(lines), increment)]

    # Le parti sono suddivise ulteriormente in base al numero di processi paralleli
    splitted_read_lines_for_process = [splitted_read_lines[i:i + int(len(splitted_read_lines) / args.n)] for i in
                                       range(0, len(splitted_read_lines), int(len(splitted_read_lines) / args.n))]

    # Se ci sono più parti di quelle necessarie per il numero
    # di processi paralleli, l'ultima parte viene aggiunta alla penultima.
    if len(splitted_read_lines_for_process) > 1:
        obj_for_proc = len(splitted_read_lines) / args.n
        if isinstance(obj_for_proc, float):
            splitted_read_lines_for_process[len(splitted_read_lines_for_process) - 2] = splitted_read_lines_for_process[
                                                                                            len(
                                                                                                splitted_read_lines_for_process) - 2] + \
                                                                                        splitted_read_lines_for_process[
                                                                                            len(
                                                                                                splitted_read_lines_for_process) - 1]

            splitted_read_lines_for_process = splitted_read_lines_for_process[:len(splitted_read_lines_for_process) - 1]

    # Il codice crea un pool di processi paralleli (Pool) e mappa la funzione
    # schema_testing_reads_fusion_mp sui dati divisi. I risultati sono poi aggregati.
    with Pool(args.n) as pool:
        func = partial(schema_testing_reads_fusion_mp, args, dataset_path, dataset_name_fasta)

        read_lines = []
        for res in pool.map(func, splitted_read_lines_for_process):
            read_lines = read_lines + res

    # Le linee risultanti sono modificate (trasformate in maiuscolo) e scritte
    # in un nuovo file di testo (test_fusion_result_CFL_ICFL_COMB-30_K8.txt).
    read_lines = [s.upper() for s in read_lines]

    # Results txt file
    dataset_name = dataset_name_fasta.replace(".fastq", "")
    test_result_file = open(dataset_path + "test_fusion_result_CFL_ICFL_COMB-30_K8_" + dataset_name + ".txt", 'w')
    test_result_file.writelines(read_lines)
    test_result_file.close()


########################################################################################################################

def schema_testing_reads_fusion_mp(args, dataset_path, dataset_name_fasta, reads=[]):
    input_fasta = dataset_path + dataset_name_fasta

    # EXTRACT READS ####################################################################################################
    read_lines = extract_reads_mp(input_fasta, reads)
    if len(read_lines) == 0:
        print('No reads extracted!')
        read_lines = []
        return read_lines

    read_lines = [s.upper() for s in read_lines]
    # print(read_lines)

    print('# READS: ', len(read_lines))

    # COMPUTE FINGERPRINTS #############################################################################################
    type_factorization = args.type_factorization

    # Check type factorization
    factorization = None
    T = None
    if type_factorization == "CFL":
        factorization = CFL
    elif type_factorization == "ICFL":
        factorization = ICFL_recursive
    elif type_factorization == "CFL_ICFL-10":
        factorization = CFL_icfl
        T = 10
    elif type_factorization == "CFL_ICFL-20":
        factorization = CFL_icfl
        T = 20
    elif type_factorization == "CFL_ICFL-30":
        factorization = CFL_icfl
        T = 30
    elif type_factorization == "CFL_COMB":
        factorization = d_cfl
    elif type_factorization == "ICFL_COMB":
        factorization = d_icfl
    elif type_factorization == "CFL_ICFL_COMB-10":
        factorization = d_cfl_icfl
        T = 10
    elif type_factorization == "CFL_ICFL_COMB-20":
        factorization = d_cfl_icfl
        T = 20
    elif type_factorization == "CFL_ICFL_COMB-30":
        factorization = d_cfl_icfl
        T = 30

    dictionary = None
    dictionary_lines = None
    if args.dictionary == 'yes':
        dictionary = open("%s" % args.path + "dictionary_" + args.type_factorization + ".txt", 'r')
        dictionary_lines = dictionary.readlines()
        dictionary_lines = [line.replace('\n', '') for line in dictionary_lines]

    res = compute_split_fingerprint_by_list(args.fact, factorization, T, args.dictionary, dictionary_lines, read_lines)
    ####################################################################################################################

    # TEST READS #######################################################################################################
    # Best model
    best_model_path = args.path + args.best_model
    list_best_model = pickle.load(open(best_model_path, "rb"))

    res = test_reads_fusion(list_best_model, args.path, args.type_factorization, args.k_value, res)
    ####################################################################################################################

    return res


# args.step = 'analyze_test_fusion' ##########################################################################################
# def analyze_reads_fusion_mp_step(args):
def gene_fusion_count(testing_path, gene_count_path, result_file, type_factorization, dataset_name_fastq):
    # result_file_path = args.path + args.result_file

    dataset_name = dataset_name_fastq.replace(".fastq", "")

    result_file_path = testing_path + result_file
    result_file = open(result_file_path)

    result_lines = result_file.readlines()

    # Remove '['
    result_lines = [s.replace('[', '') for s in result_lines]

    # Remove ']'
    result_lines = [s.replace(']', '') for s in result_lines]

    # Remove '\n'
    result_lines = [s.replace('\n', '') for s in result_lines]

    # file = open("%s" % args.path + "gene_fusion_count_" + args.type_factorization + ".txt", 'w')
    gene_fusion_count_file = open(
        "%s" % gene_count_path + "gene_fusion_count_" + type_factorization + "_" + dataset_name + ".txt",
        'w')
    gene_fusion_count_lines = []

    threshold = 95
    count_fusion = 0

    for line in result_lines:
        line = line.split('- PREDICTION:')
        line = line[1]

        line = line.split()

        line_dictionary = {}
        for s in line:
            if s in line_dictionary:
                count = line_dictionary[s]
                count = count + 1
                line_dictionary[s] = count
            else:
                line_dictionary[s] = 1

        # sort dictionary by value
        line_dictionary = {k: v for k, v in sorted(line_dictionary.items(), key=lambda item: item[1])}

        list_genes_counted = []
        for key, value in line_dictionary.items():
            s = str(key) + ':' + str(value)
            list_genes_counted.append(s)

        list_genes_counted = list_genes_counted[::-1]

        new_line = ' '.join(str(gene_count) + ' - ' for gene_count in list_genes_counted) + '\n'
        gene_fusion_count_lines.append(new_line)

    gene_fusion_count_file.writelines(gene_fusion_count_lines)
    gene_fusion_count_file.close()


def parse_gene_fusion_result(gene_fusion_count_path, dataset_name_fastq):
    dataset_name = dataset_name_fastq.replace(".fastq", "")

    # Creazione dizionario
    file_genes = open('Combinatorics_ML_Gene_Fusion/testing/RF_kfinger_clsf_report_CFL_ICFL_COMB-30_K8.csv')

    genes_lines = file_genes.readlines()
    genes_dictionary = {}
    for i in range(1, len(genes_lines)):
        line = genes_lines[i]
        line = line.split(',')

        value = line[0]
        key = i - 1

        genes_dictionary[key] = value

    file_genes.close()

    # parse results
    file_result = open(gene_fusion_count_path + 'gene_fusion_count_CFL_ICFL_COMB-30_K8_' + dataset_name + '.txt')
    result_lines = file_result.readlines()

    file_parsed = open(gene_fusion_count_path + 'parsed_gene_fusion_count_CFL_ICFL_COMB-30_K8_' + dataset_name + '.txt',
                       'w')
    parsed_lines = []

    for line in result_lines:
        line = line.split('-')

        new_line = ''
        for l in line:
            l = l.split(':')
            if l[0] == ' \n':
                continue
            id_gene = int(l[0])
            count_gene = l[1]

            label_gene = genes_dictionary[id_gene]
            new_line = new_line + label_gene + ':' + str(count_gene) + ' - '

        parsed_lines.append(new_line[:len(new_line) - 3] + '\n')

    file_parsed.writelines(parsed_lines)
    file_parsed.close()


def analyze_gene_fusion(testing_path, gene_fusion_count_path, dataset_name_fastq):
    dataset_name = dataset_name_fastq.replace(".fastq", "")

    # I 2 files hanno una corrispondenza biunivoca: riga i in "file_parsed" corrisponde a riga i in "file_result"
    file_parsed = open(gene_fusion_count_path + 'parsed_gene_fusion_count_CFL_ICFL_COMB-30_K8_' + dataset_name + '.txt')
    file_result = open(testing_path + 'test_fusion_result_CFL_ICFL_COMB-30_K8_' + dataset_name + '.txt')
    file_no_criterion = open(testing_path + 'no_fusion_criterion_CFL_ICFL_COMB-30_K8_' + dataset_name + '.txt', 'w')

    parsed_lines = file_parsed.readlines()
    result_lines = file_result.readlines()
    no_criterion_lines = []

    count_checked = 0
    i = 1
    for parsed_line, result_line in zip(parsed_lines, result_lines):

        # Estraiamo i 2 geni di fusione da "file_result" ###############################################################
        l = result_line.split()
        l = l[1].split('--')

        l1 = l[0].split('|')
        l1 = l1[1].split('.')

        fusion_gene_1 = l1[0]

        l2 = l[1].split('|')
        l2 = l2[1].split('.')

        fusion_gene_2 = l2[0]
        ################################################################################################################

        # 2) Controlliamo se i 2 geni sono tra i primi 3 elementi in "parsed_file" #####################################
        parsed = parsed_line.split('-')

        l1 = parsed[0].split(':')
        parsed_gene_1 = l1[0]
        parsed_gene_1 = parsed_gene_1.split()[0]

        if len(parsed) == 1:
            no_criterion_lines.append(result_line)
            no_criterion_lines.append(parsed_line)
            continue

        # print(parsed)

        l2 = parsed[1].split(':')

        parsed_gene_2 = l2[0]
        parsed_gene_2 = parsed_gene_2.split()[0]

        if len(parsed) > 2:
            l3 = parsed[2].split(':')
            parsed_gene_3 = l3[0]
            parsed_gene_3 = parsed_gene_3.split()[0]

        check_list = []
        if len(parsed) > 2:
            check_list = [parsed_gene_1, parsed_gene_2, parsed_gene_3]
        else:
            check_list = [parsed_gene_1, parsed_gene_2]

        # controlliamo se fusion_gene_1 e fusion_gene_2 sono in check_list
        if fusion_gene_1 in check_list and fusion_gene_2 in check_list:
            count_checked += 1
        else:
            no_criterion_lines.append('i: ' + str(i) + '\n')
            no_criterion_lines.append(result_line)
            no_criterion_lines.append(parsed_line + '\n')

        i = i + 1
        ################################################################################################################

    accuracy = float((count_checked * 100) / len(parsed_lines))
    print('% of fusion genes into the first 3 positions: {}'.format(accuracy))

    file_no_criterion.writelines(no_criterion_lines)

    file_parsed.close()
    file_result.close()
    file_no_criterion.close()


# SEARCH OPTIMAL THRESHOLD FOR DATASET (CHIMERIC + NON CHIMERIC) FOR OPTIMAL METRICS
def search_range_threshold(function, function_name, testing_path_result, gene_fusion_count_path, statistics_path,
                           dataset_path_chimeric,
                           dataset_path_non_chimeric, dataset_name_chimeric_fastq, dataset_name_non_chimeric_fastq,
                           num_lines_for_read, target_f1_score,
                           threshold_search_range, threshold_search_step):
    """
    Search for the optimal threshold using an exhaustive search.

    Parameters:
    - function: The statistical analysis function to be applied.
    - dataset_path_chimeric: Path for chimeric data.
    - dataset_path_non_chimeric: Path for non-chimeric data.
    - dataset_name_chimeric: Dataset name for chimeric data.
    - dataset_name_non_chimeric: Dataset name for non-chimeric data.
    - num_lines_for_read: Number of lines for reading data.
    - dataset_name_chimeric_fastq: Dataset name for chimeric FASTQ data.
    - dataset_name_non_chimeric_fastq: Dataset name for non-chimeric FASTQ data.
    - target_f1_score: Target F1-score for finding optimal threshold.
    - threshold_search_range: Range for searching threshold (tuple, e.g., (0, 100)).
    - threshold_search_step: Step size for threshold search.
    """
    dataset_name_chimeric = dataset_name_chimeric_fastq.replace(".fastq", "")
    dataset_name_non_chimeric = dataset_name_non_chimeric_fastq.replace(".fastq", "")

    # Percorso del file di log
    log_path = os.path.join(testing_path_result, 'log/')
    log_file_path = os.path.join(log_path, 'logfile_' + function_name + '.log')

    # Verifica se il file di log esiste e, se sì, eliminalo
    if os.path.exists(log_file_path):
        os.remove(log_file_path)

    # Logger configuration

    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    best_f1_score = 0
    flag_target_f1_score = False
    optimal_threshold = None
    optimal_metrics = None

    # threshold_search_range[0] = START_THRSHOLD    threshold_search_range[1] = END_THRESHOLD
    current_threshold = threshold_search_range[0]
    while current_threshold <= threshold_search_range[1]:

        # print("current_threshold: ", current_threshold)
        # Reset metrics for each threshold
        metrics_counter = MetricsCounter()

        # Apply statistical analysis function to chimeric data with current threshold
        function(testing_path_result, gene_fusion_count_path, dataset_path_chimeric,
                 statistics_path + f'statistics_{function_name}_{dataset_name_chimeric}.txt',
                 num_lines_for_read, dataset_name_chimeric_fastq, current_threshold, metrics_counter)

        # Apply statistical analysis function to non-chimeric data with current threshold
        function(testing_path_result, gene_fusion_count_path, dataset_path_non_chimeric,
                 statistics_path + f'statistics_{function_name}_{dataset_name_non_chimeric}.txt',
                 num_lines_for_read, dataset_name_non_chimeric_fastq, current_threshold, metrics_counter)

        # Calculate F1-score
        metrics_out = metrics_counter.calculate_metrics()

        # print(metrics_out)

        current_f1_score = metrics_counter.f1_score

        # metrics_counter.print_raw_metrics()

        # Registra le informazioni nel file di log
        logging.info(f"Current Threshold: [{current_threshold}]")
        logging.info(metrics_out)
        logging.info(
            f"Metrics: TP: {metrics_counter.tp} - FP: {metrics_counter.fp} - TN: {metrics_counter.tn} - FN: {metrics_counter.fn}")

        logging.info(f"CHIMERIC: {metrics_counter.chimeric} - NON CHIMERIC: {metrics_counter.non_chimeric}\n\n")

        # Se f1 score attuale è migliore o uguale di quello previsto e se non ha mai superato il target(flag = false)
        if current_f1_score >= target_f1_score and flag_target_f1_score == False:
            best_f1_score = current_f1_score
            optimal_threshold = current_threshold
            optimal_metrics = metrics_counter
            flag_target_f1_score = True

        # Se il flag = true, allora controllo solo che l'f1 score attuale sia migliore dell'f1 score ottimale attuale
        elif current_f1_score > best_f1_score:
            best_f1_score = current_f1_score
            optimal_threshold = current_threshold
            optimal_metrics = metrics_counter

        elif current_f1_score == best_f1_score:
            if metrics_counter.tp > optimal_metrics.tp:
                best_f1_score = current_f1_score
                optimal_threshold = current_threshold
                optimal_metrics = metrics_counter

            elif metrics_counter.fp < optimal_metrics.fp:
                best_f1_score = current_f1_score
                optimal_threshold = current_threshold
                optimal_metrics = metrics_counter
            elif metrics_counter.fn < optimal_metrics.fn:
                best_f1_score = current_f1_score
                optimal_threshold = current_threshold
                optimal_metrics = metrics_counter

        if current_threshold < threshold_search_range[1]:
            current_threshold += threshold_search_step
        else:
            logging.info(f"OPTIMAL THRESHOLD: [{optimal_threshold}]")
            return optimal_threshold

    logging.info(f"OPTIMAL THRESHOLD: [{optimal_threshold}]")

    return optimal_threshold


# SEARCH OPTIMAL THRESHOLD AND PERFORM STATISTICAL ANALYSIS( known_genes_consecutive_frequency or other)
def perform_statistical_analysis(function, testing_path_result, gene_fusion_count_path, statistics_path,
                                 dataset_path_chimeric,
                                 dataset_path_non_chimeric,
                                 dataset_name_chimeric_fastq,
                                 dataset_name_non_chimeric_fastq, num_lines_for_read, threshold_search_range,
                                 threshold_search_step):
    dataset_name_chimeric = dataset_name_chimeric_fastq.replace(".fastq", "")
    dataset_name_non_chimeric = dataset_name_non_chimeric_fastq.replace(".fastq", "")
    """
    Perform statistical analysis with known genes for a specific method.

    Parameters:
    - function: The statistical analysis function to be applied.
    - testing_path_chimeric: Path for chimeric data.
    - testing_path_non_chimeric: Path for non-chimeric data.
    - dataset_name_chimeric: Dataset name for chimeric data.
    - dataset_name_non_chimeric: Dataset name for non-chimeric data.
    - num_lines_for_read: Number of lines for reading data.
    - dataset_name_chimeric_fastq: Dataset name for chimeric FASTQ data.
    - dataset_name_non_chimeric_fastq: Dataset name for non-chimeric FASTQ data.
    - thresold: Threshold value.
    """
    # Reset metrics for statistical method
    metrics_counter = MetricsCounter()

    function_name = str(function.__name__).replace("statistical_", "")

    num_min_chimeric = 500

    # threshold_search_range = (0.1, 5)
    # threshold_search_step = 0.1
    print(threshold_search_step)
    print(threshold_search_range)
    target_f1_score = 0.90

    # DA MODIFICARE PER COMPLETARE TOOL WEB APP
    #
    # # Search in range threshold
    optimal_threshold = search_range_threshold(function, function_name, testing_path_result, gene_fusion_count_path,
                                               statistics_path, dataset_path_chimeric,
                                               dataset_path_non_chimeric,
                                               dataset_name_chimeric_fastq,
                                               dataset_name_non_chimeric_fastq,
                                               num_lines_for_read, target_f1_score,
                                               threshold_search_range, threshold_search_step)

    if optimal_threshold is not None:
        print(f"Optimal Threshold found: {optimal_threshold}")
    else:
        optimal_threshold = 1
        print("Optimal Threshold not found. Using default.")

    # Apply statistical analysis function to chimeric data
    function(testing_path_result, gene_fusion_count_path, dataset_path_chimeric,
             statistics_path + f'statistics_{function_name}_{dataset_name_chimeric}.txt',
             num_lines_for_read, dataset_name_chimeric_fastq, optimal_threshold, metrics_counter)

    # Apply statistical analysis function to non-chimeric data
    function(testing_path_result, gene_fusion_count_path, dataset_path_non_chimeric,
             statistics_path + f'statistics_{function_name}_{dataset_name_non_chimeric}.txt',
             num_lines_for_read, dataset_name_non_chimeric_fastq, optimal_threshold, metrics_counter)

    # Print results if available
    # metrics_counter.print_num_chimeric_nonChimeric()

    metrics_out = metrics_counter.calculate_metrics()
    print(metrics_out)

    metrics_path = os.path.join(testing_path_result, 'metrics/')
    ensure_dir(metrics_path)

    metrics_counter.save_csv_metric(metrics_path + "metrics_statistics_" + function_name + ".csv")
    metrics_counter.print_raw_metrics()

    # compute_fusion_accuracy(metrics_path,
    #                         statistics_path + f'statistics_{function_name}_{dataset_name_chimeric}.txt',
    #                         statistics_path + f'statistics_{function_name}_{dataset_name_non_chimeric}.txt',
    #                         function_name)
    compute_fusion_accuracy_from_logs(testing_path_result, metrics_path, "logfile_" + function_name + ".log", optimal_threshold, function_name)

    print("\n")


def compute_fusion_accuracy_and_statistics(args, num_lines_for_read):
    # Definizioni variabili da argomenti (args)
    dataset_path_chimeric = args.path1
    dataset_path_non_chimeric = args.path2
    testing_path_result = args.testing_path

    dataset_name_chimeric_fastq = args.fasta1
    dataset_name_chimeric = dataset_name_chimeric_fastq.replace(".fastq", "")

    dataset_name_non_chimeric_fastq = args.fasta2
    dataset_name_non_chimeric = dataset_name_non_chimeric_fastq.replace(".fastq", "")

    threshold_search_range = args.threshold_search_range
    threshold_search_step = float(args.threshold_search_step)

    # Create gene_fusion_count dir
    gene_fusion_count_path = os.path.join(testing_path_result, 'gene_fusion_count/')
    ensure_dir(gene_fusion_count_path)

    # 1) COUNT: genera file contenente la lista dei geni ordinati per numero di occorrenze
    gene_fusion_count(testing_path_result, gene_fusion_count_path,
                      'test_fusion_result_CFL_ICFL_COMB-30_K8_' + dataset_name_chimeric + '.txt',
                      'CFL_ICFL_COMB-30_K8', dataset_name_chimeric_fastq)

    gene_fusion_count(testing_path_result, gene_fusion_count_path,
                      'test_fusion_result_CFL_ICFL_COMB-30_K8_' + dataset_name_non_chimeric + '.txt',
                      'CFL_ICFL_COMB-30_K8', dataset_name_non_chimeric_fastq)

    # 2) PARSE: prende il file generato al passo precedente e sostituisce gli id numerici dei geni con le label
    parse_gene_fusion_result(gene_fusion_count_path, dataset_name_chimeric_fastq)
    parse_gene_fusion_result(gene_fusion_count_path, dataset_name_non_chimeric_fastq)

    # 3) ANALYZE: calcoliamo la % di reads che hanno i due geni di fusione tra i primi 3 elementi
    analyze_gene_fusion(testing_path_result, gene_fusion_count_path, dataset_name_chimeric_fastq)
    analyze_gene_fusion(testing_path_result, gene_fusion_count_path, dataset_name_non_chimeric_fastq)

    # 4) Statistical Analysis using the "break fusion index"
    #   - Per ogni read abbiamo 4 righe:
    #       a) riga 0: read corrispondente (in 'reads-both.fastq')
    #       a) riga 1: riga corrispondente nel file "test.........txt"
    #       b) riga 2: riga corrispondente nel file "parsed.........txt"
    #       c) riga 3: dice il punto di break (come posizione o numero kfinger) '$' ID_gene + classificato prima del break '$' ID_gene + classificato dopo il break
    # statistical_analysis_with_break_index(testing_path_chimeric, num_lines_for_read, dataset_name_chimeric_fastq)
    # statistical_analysis_with_break_index(testing_path_non_chimeric, num_lines_for_read,dataset_name_non_chimeric_fastq)
    # 5) Statistical Analysis using the "2 known genes"
    #   - Per ogni read abbiamo 4 righe:
    #       a) riga 0: read corrispondente (in 'reads-both.fastq')
    #       a) riga 1: riga corrispondente nel file "test.........txt"
    #       b) riga 2: riga corrispondente nel file "parsed.........txt"
    #       c) riga 3: dice il punto di break (come posizione o numero kfinger) '$' ID_gene + classificato prima del break '$' ID_gene + classificato dopo il break

    # Create gene_fusion_count dir
    statistics_path = os.path.join(testing_path_result, 'statistics/')
    ensure_dir(statistics_path)
    log_dir = os.path.join(testing_path_result, 'log/')
    ensure_dir(log_dir)

    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # statistical_analysis_with_known_genes_check_range_majority
    perform_statistical_analysis(statistical_analysis_with_known_genes_check_range_majority, testing_path_result,
                                 gene_fusion_count_path, statistics_path,
                                 dataset_path_chimeric, dataset_path_non_chimeric,
                                 dataset_name_chimeric_fastq, dataset_name_non_chimeric_fastq,
                                 num_lines_for_read, threshold_search_range, threshold_search_step)
    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # statistical_analysis_with_known_genes_no_check_range_majority
    perform_statistical_analysis(statistical_analysis_with_known_genes_no_check_range_majority, testing_path_result,
                                 gene_fusion_count_path, statistics_path,
                                 dataset_path_chimeric,
                                 dataset_path_non_chimeric, dataset_name_chimeric_fastq,
                                 dataset_name_non_chimeric_fastq,
                                 num_lines_for_read, threshold_search_range, threshold_search_step)

    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # statistical_analysis_with_known_genes_consecutive_frequency

    perform_statistical_analysis(statistical_analysis_with_known_genes_consecutive_frequency, testing_path_result,
                                 gene_fusion_count_path, statistics_path,
                                 dataset_path_chimeric,
                                 dataset_path_non_chimeric, dataset_name_chimeric_fastq,
                                 dataset_name_non_chimeric_fastq,
                                 num_lines_for_read, threshold_search_range, threshold_search_step)

    # --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


def compute_only_fusion_accuracy(args, num_lines_for_read):
    # Definizioni variabili da argomenti (args)
    dataset_path_chimeric = args.path1
    dataset_path_non_chimeric = args.path2
    testing_path_result = args.testing_path

    dataset_name_chimeric_fastq = args.fasta1
    dataset_name_chimeric = dataset_name_chimeric_fastq.replace(".fastq", "")

    dataset_name_non_chimeric_fastq = args.fasta2
    dataset_name_non_chimeric = dataset_name_non_chimeric_fastq.replace(".fastq", "")

    # Reset metrics for statistical method
    metrics_counter = MetricsCounter()

    metrics_out = metrics_counter.calculate_metrics()
    print(metrics_out)

    metrics_path = os.path.join(testing_path_result, 'metrics/')
    ensure_dir(metrics_path)

    # metrics_counter.save_csv_metric(metrics_path + "metrics_statistics_" + function_name + ".csv")
    metrics_counter.print_raw_metrics()

    # compute_fusion_accuracy(metrics_path,
    #                         statistics_path + f'statistics_{function_name}_{dataset_name_chimeric}.txt',
    #                         statistics_path + f'statistics_{function_name}_{dataset_name_non_chimeric}.txt',
    #                         function_name)
    #
    # compute_fusion_accuracy(metrics_path,
    #                         statistics_path + f'statistics_{function_name}_{dataset_name_chimeric}.txt',
    #                         statistics_path + f'statistics_{function_name}_{dataset_name_non_chimeric}.txt',
    #                         function_name)
    #
    # compute_fusion_accuracy(metrics_path,
    #                         statistics_path + f'statistics_{function_name}_{dataset_name_chimeric}.txt',
    #                         statistics_path + f'statistics_{function_name}_{dataset_name_non_chimeric}.txt',
    #                         function_name)


# Funzione per convertire l'intervallo da stringa a tupla di float
def parse_range(range_str):
    try:
        min_val, max_val = map(float, range_str.split(','))
        return (min_val, max_val)
    except ValueError:
        raise argparse.ArgumentTypeError("L'intervallo deve essere fornito come 'min,max'")


##################################################### MAIN #############################################################
########################################################################################################################
if __name__ == '__main__':
    # os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

    # Gestione argomenti ###############################################################################################
    parser = argparse.ArgumentParser()
    parser.add_argument('--step', dest='step', action='store', default='1rf')
    parser.add_argument('--path', dest='path', action='store', default='testing/')
    parser.add_argument('--path1', dest='path1', action='store', default='testing/chimeric')
    parser.add_argument('--path2', dest='path2', action='store', default='testing/non_chimeric')
    parser.add_argument('--testing_path', dest='testing_path', action='store', default='testing/test_result/')
    parser.add_argument('--fasta1', dest='fasta1', action='store', default='sample_10M_genes.fastq.gz')
    parser.add_argument('--fasta2', dest='fasta2', action='store', default='sample_10M_genes.fastq.gz')
    parser.add_argument('--result_file', dest='result_file', action='store',
                        default='test_fusion_result_CFL_ICFL_COMB-30_K8.txt')
    parser.add_argument('--fact', dest='fact', action='store', default='no_create')
    parser.add_argument('--shift', dest='shift', action='store', default='no_shift')
    parser.add_argument('--best_model', dest='best_model', action='store', default='RF_CFL_ICFL-20_K8.pickle')
    parser.add_argument('--k_type', dest='k_type', action='store', default='extended')
    parser.add_argument('--k_value', dest='k_value', action='store', default=3, type=int)
    parser.add_argument('--filter', dest='filter', action='store', default='list')
    parser.add_argument('--random', dest='random', action='store', default='no_random')
    parser.add_argument('--type_factorization', dest='type_factorization', action='store', default='CFL')
    parser.add_argument('--dictionary', dest='dictionary', action='store', default='no')
    parser.add_argument('-n', dest='n', action='store', default=1, type=int)
    # Aggiungi il parsing dell'intervallo come tupla di float
    parser.add_argument('--threshold_search_range', type=parse_range, help="Intervallo come 'min,max' (es. '0.1, 5')")
    parser.add_argument('--threshold_search_step', action='store', default=0.1, type=float)

    args = parser.parse_args()

    # prova_testing_reads_RF_fingerprint_mp_step('testing/', 'example_sample_10M_genes.fastq.gz', 'list', 'ICFL_COMB', 'no_create', 'no_shift', 'RF_fingerprint_classifier_ICFL_COMB.pickle')

    if args.step == 'test_fusion':
        print('\nTesting Step: TEST set of READS with FUSION on Best k-finger classification...\n')
        dataset_path_chimeric = args.path1
        dataset_name_chimeric = args.fasta1

        dataset_path_non_chimeric = args.path2
        dataset_name_non_chimeric = args.fasta2
        testing_reads_fusion_mp_step(args, dataset_path_chimeric, dataset_name_chimeric)
        testing_reads_fusion_mp_step(args, dataset_path_non_chimeric, dataset_name_non_chimeric)
        # dataset_name_fastq = args.fasta

    if args.step == 'test_result':
        print("\nCreate Statistics file and compute fusion score")
        compute_fusion_accuracy_and_statistics(args, 2)

    if args.step == 'compute_only_result':
        # Compute only fusion accuracy
        compute_only_fusion_accuracy(args, 2)
