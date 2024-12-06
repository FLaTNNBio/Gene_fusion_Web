import operator

from Combinatorics_ML_Gene_Fusion.combinatorics_metrics import MetricsCounter


def most_common(lst):
    # CONTROLLA CHE LA LISTA DI GENI IN INPUT(PRIMA DEL BREAK O DOPO IL BREAK) NON SIA NULL
    if len(lst) != 0:
        return max(set(lst), key=lst.count)
    else:
        return []


def most_consecutive_frequent(lst):
    # Create genes dictionary and initialize each to 0
    g_dictionary = {}
    for g in lst:
        value = 0
        key = g

        g_dictionary[key] = value

    # Count consecutive frequency for each gene
    for i in range(1, len(lst)):
        if lst[i] == lst[i - 1]:
            value = g_dictionary[lst[i]]
            value += 1
            g_dictionary[lst[i]] = value

    return max(g_dictionary.items(), key=operator.itemgetter(1))[0]


def smooth_range(lst=[], threshold=1):
    target_gene = lst[0]
    target_gene_positions = [i for i, val in enumerate(lst) if val == target_gene]

    # scorro left-to-right fino a che non trovo 2 elementi consecutivi <= threshold
    start_index = 0
    for i in range(1, len(target_gene_positions)):

        if target_gene_positions[i] - target_gene_positions[i - 1] <= threshold:
            start_index = target_gene_positions[i - 1]
            break

    # scorro right-to-left fino a che non trovo 2 elementi consecutivi <= threshold
    end_index = len(target_gene_positions) - 1
    for i in range(len(target_gene_positions) - 2, 0, -1):

        if target_gene_positions[i + 1] - target_gene_positions[i] <= threshold:
            end_index = target_gene_positions[i + 1]
            break

    if end_index == len(target_gene_positions) - 1:
        lst = lst[start_index:len(target_gene_positions)]
    else:
        lst = lst[start_index:end_index + 1]

    return lst




def statistical_analysis_with_break_index(testing_path, gene_fusion_count_path, dataset_path,rf_kfinger_clsf_report, num_line_for_read,
                                          dataset_name_fastq="reads-both.fastq"):
    dataset_name = dataset_name_fastq.replace(".fastq", "")
    # Pre-processing ###################################################################################################
    # open files
    file_test = open(testing_path + 'test_fusion_result_CFL_ICFL_COMB-30_K8_' + dataset_name + '.txt')
    file_parsed = open(gene_fusion_count_path + 'parsed_gene_fusion_count_CFL_ICFL_COMB-30_K8_' + dataset_name + '.txt')
    file_reads = open(dataset_path + dataset_name_fastq)

    # create new file
    file_statistics = open(testing_path + 'statistics_CFL_ICFL_COMB-30_K8_' + dataset_name + '.txt', 'w')

    # read lines
    test_lines = file_test.readlines()
    parsed_lines = file_parsed.readlines()
    reads_lines = file_reads.readlines()

    statistics_lines = []

    # Creazione dizionario
    file_genes = open('Combinatorics_ML_Gene_Fusion/training/models/'+rf_kfinger_clsf_report)

    genes_lines = file_genes.readlines()
    genes_dictionary = {}
    for i in range(1, len(genes_lines)):
        line = genes_lines[i]
        line = line.split(',')

        value = line[0]
        key = i - 1

        genes_dictionary[key] = value

    file_genes.close()
    ####################################################################################################################

    # For each read create the lines in 'statistics_CFL_ICFL_COMB-30_K8.txt'
    for i in range(len(test_lines)):

        test_line = test_lines[i]
        parsed_line = parsed_lines[i]

        # Find corresponding read in 'dataset_name_fastq' ################################################################
        start_index = i * num_line_for_read
        end_index = start_index + num_line_for_read
        lines_for_current_read = reads_lines[start_index:end_index]
        read_line = lines_for_current_read[1]

        # INDIVIDUAZIONE break fusion index -- "DA CAMBIARE CON IL DATO DI YURI" #######################################
        break_fusion_index = -1  # posizione nella read in cui comincia finisce un gene ed inizia l'altro
        for j, c in enumerate(read_line):
            if not c.isupper():
                break_fusion_index = j
                break
        ################################################################################################################

        # Find most occurrent Gene_1 BEFORE break_fusion_index and Gene_2 AFTER break_fusion_index #####################
        # a) get list of kfinger predictions from test_line
        test_line_lst = test_line.split(' - PREDICTION: ')

        # b) splittiamo tra la prima parte contenente la sequenza di lunghezze e la seconda parte contenente le predictions
        # l'i-esimo elemento di kfingers_line_lst corrisponde all'i-esimo elemento di gene_line_lst
        kfingers_line_lst = test_line_lst[0]
        gene_line_lst = test_line_lst[1]

        kfingers_line_lst = kfingers_line_lst.split('|')
        kfingers_line_lst = kfingers_line_lst[3:]

        gene_line_lst = gene_line_lst.split('] [')
        gene_line_lst = gene_line_lst[1:]

        # splittiamo i geni contenuti in test_line_lst in 2 liste: prima di break_fusion_index e dopo break_fusion_index
        genes_before_break_fusion = []
        genes_after_break_fusion = []

        current_position = 0

        for kfinger_line, gene_line in zip(kfingers_line_lst, gene_line_lst):
            kfinger_line = kfinger_line.split()
            gene_line = gene_line.split()
            for j, g in enumerate(gene_line):
                if j < len(gene_line) - 1:
                    current_position += int(kfinger_line[j])
                else:
                    for k in range(j, len(kfinger_line)):
                        current_position += int(kfinger_line[k])

                current_g = g.replace('[', '')
                current_g = current_g.replace(']', '')
                current_g = current_g.replace(' ', '')

                label_gene = genes_dictionary[int(current_g)]

                if current_position <= break_fusion_index:
                    genes_before_break_fusion.append(label_gene)
                else:
                    genes_after_break_fusion.append(label_gene)

        # c) count genes in genes_before_break_fusion and genes_after_break_fusion

        gene_before = most_common(genes_before_break_fusion)
        gene_after = most_common(genes_after_break_fusion)
        ################################################################################################################

        ################################################################################################################
        # Add lines in 'statistics_CFL_ICFL_COMB-30_K8.txt'
        read_line = read_line.replace('\n', '')
        test_line = test_line.replace('\n', '')
        parsed_line = parsed_line.replace('\n', '')

        statistics_lines.append('READ: ' + read_line + '\n')
        statistics_lines.append('TEST_RESULT: ' + test_line + '\n')
        statistics_lines.append('SORTING GENES: ' + parsed_line + '\n')

        stastistics_line = 'STATISTICS: break_fusion_position: ' + str(break_fusion_index) + ' $ '

        # Controlla che la lista dei geni piu' frequenti PRIMA del punto di break non sia nulla
        if len(gene_before) != 0:
            stastistics_line = stastistics_line + 'first_fusion_gene: ' + gene_before + ' $ '

        # Controlla che la lista dei geni piu' frequenti DOPO il punto di break non sia nulla
        if len(gene_after) != 0:
            stastistics_line = stastistics_line + 'second_fusion_gene: ' + gene_after + '\n\n'

        statistics_lines.append(stastistics_line)

    file_statistics.writelines(statistics_lines)

    # Close files ######################################################################################################
    file_test.close()
    file_parsed.close()
    file_reads.close()
    file_statistics.close()


########################################################################################################################

def statistical_analysis_with_known_genes_check_range_majority(testing_path, gene_fusion_count_path, dataset_path,
                                                               statistics_path,
                                                               rf_kfinger_clsf_report,
                                                               num_line_for_read,
                                                               dataset_name_fastq="reads-both.fastq",
                                                               fusion_threshold=60, metrics_counter=MetricsCounter()):
    # Pre-processing ###################################################################################################
    # open files
    dataset_name = dataset_name_fastq.replace(".fastq", "")

    file_test = open(testing_path + 'test_fusion_result_CFL_ICFL_COMB-30_K8_' + dataset_name + '.txt')
    file_parsed = open(gene_fusion_count_path + 'parsed_gene_fusion_count_CFL_ICFL_COMB-30_K8_' + dataset_name + '.txt')
    file_reads = open(dataset_path + dataset_name_fastq)

    # create new file
    file_statistics = open(statistics_path, 'w')

    # read lines
    test_lines = file_test.readlines()
    parsed_lines = file_parsed.readlines()
    reads_lines = file_reads.readlines()

    statistics_lines = []

    # Creazione dizionario

    file_genes = open('Combinatorics_ML_Gene_Fusion/training/models/'+rf_kfinger_clsf_report)

    genes_lines = file_genes.readlines()
    genes_dictionary = {}
    for i in range(1, len(genes_lines)):
        line = genes_lines[i]
        line = line.split(',')

        value = line[0]
        key = i - 1

        genes_dictionary[key] = value

    file_genes.close()
    ####################################################################################################################

    # For each read create the lines in 'statistics_CFL_ICFL_COMB-30_K8.txt'
    for i in range(len(test_lines)):

        test_line = test_lines[i]
        parsed_line = parsed_lines[i]

        # Find corresponding read in 'dataset_name_fastq' ################################################################
        start_index = i * num_line_for_read
        end_index = start_index + num_line_for_read
        lines_for_current_read = reads_lines[start_index:end_index]
        read_line = lines_for_current_read[1]

        # Find most occurrent Gene_1 BEFORE break_fusion_index and Gene_2 AFTER break_fusion_index #####################
        # a) get list of kfinger predictions from test_line
        test_line_lst = test_line.split(' - PREDICTION: ')

        # b) splittiamo tra la prima parte contenente la sequenza di lunghezze e la seconda parte contenente le predictions
        kfingers_line_lst = test_line_lst[0]
        gene_line_lst = test_line_lst[1]

        # Extract the 2 reference fusion genes #########################################################################
        kfingers_line_lst = kfingers_line_lst.split('|')

        # Fusion Gene 1
        fusion_gene_1 = kfingers_line_lst[1]
        fusion_gene_1 = fusion_gene_1.split('.')
        fusion_gene_1 = fusion_gene_1[0]

        # Fusion Gene 2
        fusion_gene_2 = kfingers_line_lst[2]
        fusion_gene_2 = fusion_gene_2.split('.')
        fusion_gene_2 = fusion_gene_2[0]
        ################################################################################################################

        gene_line_lst = gene_line_lst.replace('[', '')
        gene_line_lst = gene_line_lst.replace(']', '')
        gene_line_lst = gene_line_lst.split()

        try:
            gene_line_lst = [genes_dictionary[int(g)] for g in gene_line_lst]
        except KeyError:
            # Salta alla prossima iterazione del ciclo in caso di chiave mancante
            continue

        # Add lines in 'statistics_CFL_ICFL_COMB-30_K8.txt'
        read_line = read_line.replace('\n', '')
        test_line = test_line.replace('\n', '')
        parsed_line = parsed_line.replace('\n', '')

        statistics_lines.append('READ: ' + read_line + '\n')
        statistics_lines.append('TEST_RESULT: ' + test_line + '\n')
        statistics_lines.append('SORTING GENES: ' + parsed_line + '\n')

        # Check relation between "gene 1 interval" and "gene 2 interval" ###############################################
        try:
            start_index_gene_1 = gene_line_lst.index(fusion_gene_1)
            end_index_gene_1 = len(gene_line_lst) - gene_line_lst[::-1].index(fusion_gene_1) - 1

            start_index_gene_2 = gene_line_lst.index(fusion_gene_2)
            end_index_gene_2 = len(gene_line_lst) - gene_line_lst[::-1].index(fusion_gene_2) - 1

        except ValueError:

            stastistics_line = 'NO Break Fusion Interval!' + '\n'
            stastistics_line = stastistics_line + '-\n'
            stastistics_line = stastistics_line + '-\n\n'
            statistics_lines.append(stastistics_line)

            # TN CASE
            # metrics_counter.increment_trueNegative(fusion_gene_1, fusion_gene_2)

            continue

        range_gene_1 = []
        range_gene_2 = []

        # FIRST CASE
        if start_index_gene_1 < end_index_gene_1 and start_index_gene_2 < end_index_gene_2 and end_index_gene_1 < end_index_gene_2:

            end_1 = 0
            if end_index_gene_1 == len(gene_line_lst):
                end_1 = end_index_gene_1
            else:
                end_1 = end_index_gene_1 + 1
            range_gene_1 = gene_line_lst[start_index_gene_1:end_1]
            range_gene_1 = smooth_range(lst=range_gene_1, threshold=1)

            end_2 = 0
            if end_index_gene_2 == len(gene_line_lst):
                end_2 = end_index_gene_2
            else:
                end_2 = end_index_gene_2 + 1
            range_gene_2 = gene_line_lst[start_index_gene_2:end_2]
            range_gene_2 = smooth_range(lst=range_gene_2, threshold=1)

            most_common_gene_in_range_gene_1 = most_common(range_gene_1)
            most_common_gene_in_range_gene_2 = most_common(range_gene_2)

            # Compute fusion_score
            perc_1 = ((end_1 - start_index_gene_1 + 1) * 100) / len(gene_line_lst)
            perc_2 = ((end_2 - start_index_gene_2 + 1) * 100) / len(gene_line_lst)
            perc_intersec = (len(gene_line_lst[start_index_gene_2:end_1]) * 100) / len(gene_line_lst)
            fusion_score = abs(100 - (perc_1 + perc_2 - perc_intersec))

            if fusion_score >= fusion_threshold:  # IL MODELLO DICE CHE E' CHIMERICO

                if fusion_gene_1 == fusion_gene_2:

                    stastistics_line = 'NO Break Fusion!- fusion_score:' + str(fusion_score) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                        start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_2:' + str(
                        fusion_gene_2) + ' |start_index:' + str(
                        start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                    # stastistics_line = stastistics_line + '-\n'
                    # stastistics_line = stastistics_line + '-\n\n'
                    statistics_lines.append(stastistics_line)

                    metrics_counter.increment_falsePositive(fusion_gene_1, fusion_gene_2)


                elif most_common_gene_in_range_gene_1 == fusion_gene_1 and most_common_gene_in_range_gene_2 == fusion_gene_2:

                    stastistics_line = 'YES Break Fusion - fusion_score:' + str(fusion_score) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                        start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_2:' + str(
                        fusion_gene_2) + ' |start_index:' + str(
                        start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                    statistics_lines.append(stastistics_line)

                    metrics_counter.increment_truePositive(fusion_gene_1, fusion_gene_2)

            elif fusion_score < fusion_threshold:

                if fusion_gene_1 == fusion_gene_2:

                    stastistics_line = 'NO Break Fusion! - fusion_score:' + str(fusion_score) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                        start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_2:' + str(
                        fusion_gene_2) + ' |start_index:' + str(
                        start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                    # stastistics_line = stastistics_line + '-\n'
                    # stastistics_line = stastistics_line + '-\n\n'
                    statistics_lines.append(stastistics_line)

                    metrics_counter.increment_trueNegative(fusion_gene_1, fusion_gene_2)


                elif most_common_gene_in_range_gene_1 == fusion_gene_1 and most_common_gene_in_range_gene_2 == fusion_gene_2:

                    stastistics_line = 'YES Break Fusion - fusion_score:' + str(fusion_score) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                        start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_2:' + str(
                        fusion_gene_2) + ' |start_index:' + str(
                        start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                    statistics_lines.append(stastistics_line)

                    metrics_counter.increment_falseNegative(fusion_gene_1, fusion_gene_2)

        # SECOND CASE
        elif start_index_gene_2 < end_index_gene_2 and start_index_gene_1 < end_index_gene_1 and end_index_gene_2 < end_index_gene_1:

            end_1 = 0
            if end_index_gene_1 == len(gene_line_lst):
                end_1 = end_index_gene_1
            else:
                end_1 = end_index_gene_1 + 1
            range_gene_1 = gene_line_lst[start_index_gene_1:end_1]

            end_2 = 0
            if end_index_gene_2 == len(gene_line_lst):
                end_2 = end_index_gene_2
            else:
                end_2 = end_index_gene_2 + 1
            range_gene_2 = gene_line_lst[start_index_gene_2:end_2]

            most_common_gene_in_range_gene_1 = most_common(range_gene_1)
            most_common_gene_in_range_gene_2 = most_common(range_gene_2)

            # Compute fusion_score
            perc_1 = ((end_1 - start_index_gene_1 + 1) * 100) / len(gene_line_lst)
            perc_2 = ((end_2 - start_index_gene_2 + 1) * 100) / len(gene_line_lst)
            perc_intersec = (len(gene_line_lst[start_index_gene_2:end_1]) * 100) / len(gene_line_lst)
            fusion_score = abs(100 - (perc_1 + perc_2 - perc_intersec))

            if fusion_score >= fusion_threshold:  # IL MODELLO DICE CHE E' CHIMERICO

                if fusion_gene_1 == fusion_gene_2:

                    stastistics_line = 'NO Break Fusion!- fusion_score:' + str(fusion_score) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                        start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_2:' + str(
                        fusion_gene_2) + ' |start_index:' + str(
                        start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                    # stastistics_line = stastistics_line + '-\n'
                    # stastistics_line = stastistics_line + '-\n\n'
                    statistics_lines.append(stastistics_line)

                    metrics_counter.increment_falsePositive(fusion_gene_1, fusion_gene_2)


                elif most_common_gene_in_range_gene_1 == fusion_gene_1 and most_common_gene_in_range_gene_2 == fusion_gene_2:

                    stastistics_line = 'YES Break Fusion - fusion_score:' + str(fusion_score) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                        start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_2:' + str(
                        fusion_gene_2) + ' |start_index:' + str(
                        start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                    statistics_lines.append(stastistics_line)

                    metrics_counter.increment_truePositive(fusion_gene_1, fusion_gene_2)

            elif fusion_score < fusion_threshold:

                if fusion_gene_1 == fusion_gene_2:

                    stastistics_line = 'NO Break Fusion! - fusion_score:' + str(fusion_score) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                        start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_2:' + str(
                        fusion_gene_2) + ' |start_index:' + str(
                        start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                    # stastistics_line = stastistics_line + '-\n'
                    # stastistics_line = stastistics_line + '-\n\n'
                    statistics_lines.append(stastistics_line)

                    metrics_counter.increment_trueNegative(fusion_gene_1, fusion_gene_2)


                elif most_common_gene_in_range_gene_1 == fusion_gene_1 and most_common_gene_in_range_gene_2 == fusion_gene_2:

                    stastistics_line = 'YES Break Fusion - fusion_score:' + str(fusion_score) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                        start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                    stastistics_line = stastistics_line + 'fusion_gene_2:' + str(
                        fusion_gene_2) + ' |start_index:' + str(
                        start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                    statistics_lines.append(stastistics_line)

                    metrics_counter.increment_falseNegative(fusion_gene_1, fusion_gene_2)

    ################################################################################################################

    ################################################################################################################

    file_statistics.writelines(statistics_lines)

    # Close files ######################################################################################################
    file_test.close()
    file_parsed.close()
    file_reads.close()
    file_statistics.close()

    return metrics_counter


########################################################################################################################


def statistical_analysis_with_known_genes_no_check_range_majority(testing_path, gene_fusion_count_path, dataset_path,
                                                                  statistics_path,
                                                                  rf_kfinger_clsf_report,
                                                                  num_line_for_read,
                                                                  dataset_name_fastq="reads-both.fastq",
                                                                  fusion_threshold=60,
                                                                  metrics_counter=MetricsCounter()):
    # Pre-processing ###################################################################################################
    # open files
    dataset_name = dataset_name_fastq.replace(".fastq", "")

    file_test = open(testing_path + 'test_fusion_result_CFL_ICFL_COMB-30_K8_' + dataset_name + '.txt')
    file_parsed = open(gene_fusion_count_path + 'parsed_gene_fusion_count_CFL_ICFL_COMB-30_K8_' + dataset_name + '.txt')
    file_reads = open(dataset_path + dataset_name_fastq)

    # create new file
    file_statistics = open(statistics_path, 'w')

    # read lines
    test_lines = file_test.readlines()
    parsed_lines = file_parsed.readlines()
    reads_lines = file_reads.readlines()

    statistics_lines = []

    # Creazione dizionario
    file_genes = open('Combinatorics_ML_Gene_Fusion/training/models/'+rf_kfinger_clsf_report)

    genes_lines = file_genes.readlines()
    genes_dictionary = {}
    for i in range(1, len(genes_lines)):
        line = genes_lines[i]
        line = line.split(',')

        value = line[0]
        key = i - 1

        genes_dictionary[key] = value

    file_genes.close()
    ####################################################################################################################

    # For each read create the lines in 'statistics_CFL_ICFL_COMB-30_K8.txt'
    for i in range(len(test_lines)):

        test_line = test_lines[i]
        parsed_line = parsed_lines[i]

        # Find corresponding read in 'reads-both.fastq' ################################################################
        start_index = i * num_line_for_read
        end_index = start_index + num_line_for_read
        lines_for_current_read = reads_lines[start_index:end_index]
        read_line = lines_for_current_read[1]

        # Find most occurrent Gene_1 BEFORE break_fusion_index and Gene_2 AFTER break_fusion_index #####################
        # a) get list of kfinger predictions from test_line
        test_line_lst = test_line.split(' - PREDICTION: ')

        # b) splittiamo tra la prima parte contenente la sequenza di lunghezze e la seconda parte contenente le predictions
        kfingers_line_lst = test_line_lst[0]
        gene_line_lst = test_line_lst[1]

        # Extract the 2 reference fusion genes #########################################################################
        kfingers_line_lst = kfingers_line_lst.split('|')

        # Fusion Gene 1
        fusion_gene_1 = kfingers_line_lst[1]
        fusion_gene_1 = fusion_gene_1.split('.')
        fusion_gene_1 = fusion_gene_1[0]

        # Fusion Gene 2
        fusion_gene_2 = kfingers_line_lst[2]
        fusion_gene_2 = fusion_gene_2.split('.')
        fusion_gene_2 = fusion_gene_2[0]
        ################################################################################################################

        gene_line_lst = gene_line_lst.replace('[', '')
        gene_line_lst = gene_line_lst.replace(']', '')
        gene_line_lst = gene_line_lst.split()
        try:
            gene_line_lst = [genes_dictionary[int(g)] for g in gene_line_lst]
        except KeyError:
            # Salta alla prossima iterazione del ciclo in caso di chiave mancante
            continue

        # Add lines in 'statistics_CFL_ICFL_COMB-30_K8.txt'
        read_line = read_line.replace('\n', '')
        test_line = test_line.replace('\n', '')
        parsed_line = parsed_line.replace('\n', '')

        statistics_lines.append('READ: ' + read_line + '\n')
        statistics_lines.append('TEST_RESULT: ' + test_line + '\n')
        statistics_lines.append('SORTING GENES: ' + parsed_line + '\n')

        # Check relation between "gene 1 interval" and "gene 2 interval" ###############################################
        try:
            start_index_gene_1 = gene_line_lst.index(fusion_gene_1)
            end_index_gene_1 = len(gene_line_lst) - gene_line_lst[::-1].index(fusion_gene_1) - 1

            start_index_gene_2 = gene_line_lst.index(fusion_gene_2)
            end_index_gene_2 = len(gene_line_lst) - gene_line_lst[::-1].index(fusion_gene_2) - 1

        except ValueError:

            stastistics_line = 'NO Break Fusion Interval!' + '\n'
            stastistics_line = stastistics_line + '-\n'
            stastistics_line = stastistics_line + '-\n\n'
            statistics_lines.append(stastistics_line)

            # TN CASE
            # metrics_counter.increment_trueNegative(fusion_gene_1, fusion_gene_2)

            continue

        range_gene_1 = []
        range_gene_2 = []

        end_1 = 0
        if end_index_gene_1 == len(gene_line_lst):
            end_1 = end_index_gene_1
        else:
            end_1 = end_index_gene_1 + 1
        range_gene_1 = gene_line_lst[start_index_gene_1:end_1]
        range_gene_1 = smooth_range(lst=range_gene_1, threshold=1)

        end_2 = 0
        if end_index_gene_2 == len(gene_line_lst):
            end_2 = end_index_gene_2
        else:
            end_2 = end_index_gene_2 + 1

        range_gene_2 = gene_line_lst[start_index_gene_2:end_2]
        range_gene_2 = smooth_range(lst=range_gene_2, threshold=1)

        most_common_gene_in_range_gene_1 = most_common(range_gene_1)
        most_common_gene_in_range_gene_2 = most_common(range_gene_2)

        # Compute fusion_score
        perc_1 = ((end_1 - start_index_gene_1 + 1) * 100) / len(gene_line_lst)
        perc_2 = ((end_2 - start_index_gene_2 + 1) * 100) / len(gene_line_lst)
        perc_intersec = (len(gene_line_lst[start_index_gene_2:end_1]) * 100) / len(gene_line_lst)
        fusion_score = abs(100 - (perc_1 + perc_2 - perc_intersec))

        if fusion_score >= fusion_threshold:  # IL MODELLO DICE CHE E' CHIMERICO

            if fusion_gene_1 == fusion_gene_2:

                stastistics_line = 'NO Break Fusion!- fusion_score:' + str(fusion_score) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                    start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_2:' + str(fusion_gene_2) + ' |start_index:' + str(
                    start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                # stastistics_line = stastistics_line + '-\n'
                # stastistics_line = stastistics_line + '-\n\n'
                statistics_lines.append(stastistics_line)

                metrics_counter.increment_falsePositive(fusion_gene_1, fusion_gene_2)


            elif most_common_gene_in_range_gene_1 == fusion_gene_1 and most_common_gene_in_range_gene_2 == fusion_gene_2:

                stastistics_line = 'YES Break Fusion - fusion_score:' + str(fusion_score) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                    start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_2:' + str(fusion_gene_2) + ' |start_index:' + str(
                    start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                statistics_lines.append(stastistics_line)

                metrics_counter.increment_truePositive(fusion_gene_1, fusion_gene_2)

        elif fusion_score < fusion_threshold:

            if fusion_gene_1 == fusion_gene_2:

                stastistics_line = 'NO Break Fusion! - fusion_score:' + str(fusion_score) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                    start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_2:' + str(fusion_gene_2) + ' |start_index:' + str(
                    start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                # stastistics_line = stastistics_line + '-\n'
                # stastistics_line = stastistics_line + '-\n\n'
                statistics_lines.append(stastistics_line)

                metrics_counter.increment_trueNegative(fusion_gene_1, fusion_gene_2)


            elif most_common_gene_in_range_gene_1 == fusion_gene_1 and most_common_gene_in_range_gene_2 == fusion_gene_2:

                stastistics_line = 'YES Break Fusion - fusion_score:' + str(fusion_score) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                    start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_2:' + str(fusion_gene_2) + ' |start_index:' + str(
                    start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                statistics_lines.append(stastistics_line)

                metrics_counter.increment_falseNegative(fusion_gene_1, fusion_gene_2)

        ################################################################################################################

    file_statistics.writelines(statistics_lines)

    # Close files ######################################################################################################
    file_test.close()
    file_parsed.close()
    file_reads.close()
    file_statistics.close()

    return metrics_counter


########################################################################################################################

def statistical_analysis_with_known_genes_consecutive_frequency(testing_path, gene_fusion_count_path, dataset_path,
                                                                statistics_path,
                                                                rf_kfinger_clsf_report,
                                                                num_lines_for_read,
                                                                dataset_name_fastq="reads-both.fastq",
                                                                fusion_threshold=60, metrics_counter=MetricsCounter()):
    # Pre-processing ###################################################################################################
    # open files
    dataset_name = dataset_name_fastq.replace(".fastq", "")

    file_test = open(testing_path + 'test_fusion_result_CFL_ICFL_COMB-30_K8_' + dataset_name + '.txt')
    file_parsed = open(gene_fusion_count_path + 'parsed_gene_fusion_count_CFL_ICFL_COMB-30_K8_' + dataset_name + '.txt')
    file_reads = open(dataset_path + dataset_name_fastq)

    # create new file
    file_statistics = open(statistics_path, 'w')

    # read lines
    test_lines = file_test.readlines()
    parsed_lines = file_parsed.readlines()
    reads_lines = file_reads.readlines()

    statistics_lines = []

    # Creazione dizionario
    file_genes = open('Combinatorics_ML_Gene_Fusion/training/models/'+rf_kfinger_clsf_report)

    genes_lines = file_genes.readlines()
    genes_dictionary = {}
    for i in range(1, len(genes_lines)):
        line = genes_lines[i]
        line = line.split(',')

        value = line[0]
        key = i - 1

        genes_dictionary[key] = value

    file_genes.close()
    ####################################################################################################################

    # For each read create the lines in 'statistics_CFL_ICFL_COMB-30_K8.txt'
    for i in range(len(test_lines)):

        test_line = test_lines[i]
        parsed_line = parsed_lines[i]

        # Find corresponding read in 'dataset.fastq' ################################################################
        start_index = i * num_lines_for_read
        end_index = start_index + num_lines_for_read
        lines_for_current_read = reads_lines[start_index:end_index]
        read_line = lines_for_current_read[1]

        # Find most occurrent Gene_1 BEFORE break_fusion_index and Gene_2 AFTER break_fusion_index #####################

        # a) get list of kfinger predictions from test_line
        test_line_lst = test_line.split(' - PREDICTION: ')

        # b) splittiamo tra la prima parte contenente la sequenza di lunghezze e la seconda parte contenente le predictions
        kfingers_line_lst = test_line_lst[0]
        gene_line_lst = test_line_lst[1]

        # Extract the 2 reference fusion genes #########################################################################
        kfingers_line_lst = kfingers_line_lst.split('|')

        # Fusion Gene 1
        fusion_gene_1 = kfingers_line_lst[1]
        fusion_gene_1 = fusion_gene_1.split('.')
        fusion_gene_1 = fusion_gene_1[0]

        # Fusion Gene 2
        fusion_gene_2 = kfingers_line_lst[2]
        fusion_gene_2 = fusion_gene_2.split('.')
        fusion_gene_2 = fusion_gene_2[0]
        ################################################################################################################

        gene_line_lst = gene_line_lst.replace('[', '')
        gene_line_lst = gene_line_lst.replace(']', '')
        gene_line_lst = gene_line_lst.split()
        try:
            gene_line_lst = [genes_dictionary[int(g)] for g in gene_line_lst]
        except KeyError:
            # Salta alla prossima iterazione del ciclo in caso di chiave mancante
            continue

        # Add lines in 'statistics_CFL_ICFL_COMB-30_K8.txt'
        read_line = read_line.replace('\n', '')
        test_line = test_line.replace('\n', '')
        parsed_line = parsed_line.replace('\n', '')

        statistics_lines.append('READ: ' + read_line + '\n')
        statistics_lines.append('TEST_RESULT: ' + test_line + '\n')
        statistics_lines.append('SORTING GENES: ' + parsed_line + '\n')

        start_index_gene_1 = -1
        start_index_gene_2 = -1
        end_index_gene_1 = -1
        end_index_gene_2 = -1

        # Check relation between "gene 1 interval" and "gene 2 interval" ###############################################
        try:
            start_index_gene_1 = gene_line_lst.index(fusion_gene_1)
            end_index_gene_1 = len(gene_line_lst) - gene_line_lst[::-1].index(fusion_gene_1) - 1
            start_index_gene_2 = gene_line_lst.index(fusion_gene_2)
            end_index_gene_2 = len(gene_line_lst) - gene_line_lst[::-1].index(fusion_gene_2) - 1

        except ValueError:

            stastistics_line = 'NO Break Fusion Interval!' + '\n'
            stastistics_line = stastistics_line + '-\n'
            stastistics_line = stastistics_line + '-\n\n'
            statistics_lines.append(stastistics_line)

            # TN CASE
            # metrics_counter.increment_trueNegative(fusion_gene_1, fusion_gene_2)

            continue

        range_gene_1 = []
        range_gene_2 = []

        end_1 = 0
        if end_index_gene_1 == len(gene_line_lst):
            end_1 = end_index_gene_1
        else:
            end_1 = end_index_gene_1 + 1

        range_gene_1 = gene_line_lst[start_index_gene_1:end_1]
        range_gene_1 = smooth_range(lst=range_gene_1, threshold=1)

        end_2 = 0
        if end_index_gene_2 == len(gene_line_lst):
            end_2 = end_index_gene_2
        else:
            end_2 = end_index_gene_2 + 1
        range_gene_2 = gene_line_lst[start_index_gene_2:end_2]
        range_gene_2 = smooth_range(lst=range_gene_2, threshold=1)

        most_common_gene_in_range_gene_1 = most_consecutive_frequent(range_gene_1)
        most_common_gene_in_range_gene_2 = most_consecutive_frequent(range_gene_2)

        # Compute fusion_score
        perc_1 = ((end_1 - start_index_gene_1 + 1) * 100) / len(gene_line_lst)
        perc_2 = ((end_2 - start_index_gene_2 + 1) * 100) / len(gene_line_lst)
        perc_intersec = (len(gene_line_lst[start_index_gene_2:end_1]) * 100) / len(gene_line_lst)
        fusion_score = abs(100 - (perc_1 + perc_2 - perc_intersec))

        if fusion_score >= fusion_threshold:  # IL MODELLO DICE CHE E' CHIMERICO

            if fusion_gene_1 == fusion_gene_2:

                stastistics_line = 'NO Break Fusion!- fusion_score:' + str(fusion_score) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                    start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_2:' + str(fusion_gene_2) + ' |start_index:' + str(
                    start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                # stastistics_line = stastistics_line + '-\n'
                # stastistics_line = stastistics_line + '-\n\n'
                statistics_lines.append(stastistics_line)

                metrics_counter.increment_falsePositive(fusion_gene_1, fusion_gene_2)


            elif most_common_gene_in_range_gene_1 == fusion_gene_1 and most_common_gene_in_range_gene_2 == fusion_gene_2:

                stastistics_line = 'YES Break Fusion - fusion_score:' + str(fusion_score) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                    start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_2:' + str(fusion_gene_2) + ' |start_index:' + str(
                    start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                statistics_lines.append(stastistics_line)

                metrics_counter.increment_truePositive(fusion_gene_1, fusion_gene_2)

        elif fusion_score < fusion_threshold:

            if fusion_gene_1 == fusion_gene_2:

                stastistics_line = 'NO Break Fusion! - fusion_score:' + str(fusion_score) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                    start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_2:' + str(fusion_gene_2) + ' |start_index:' + str(
                    start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                # stastistics_line = stastistics_line + '-\n'
                # stastistics_line = stastistics_line + '-\n\n'
                statistics_lines.append(stastistics_line)

                metrics_counter.increment_trueNegative(fusion_gene_1, fusion_gene_2)


            elif most_common_gene_in_range_gene_1 == fusion_gene_1 and most_common_gene_in_range_gene_2 == fusion_gene_2:

                stastistics_line = 'YES Break Fusion - fusion_score:' + str(fusion_score) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_1:' + str(fusion_gene_1) + '|start_index:' + str(
                    start_index_gene_1) + '|end_index:' + str(end_index_gene_1) + '\n'
                stastistics_line = stastistics_line + 'fusion_gene_2:' + str(fusion_gene_2) + ' |start_index:' + str(
                    start_index_gene_2) + '|end_index:' + str(end_index_gene_2) + '\n\n'
                statistics_lines.append(stastistics_line)

                metrics_counter.increment_falseNegative(fusion_gene_1, fusion_gene_2)

        ################################################################################################################

        ################################################################################################################

    file_statistics.writelines(statistics_lines)

    # Close files ######################################################################################################
    file_test.close()
    file_parsed.close()
    file_reads.close()
    file_statistics.close()

    return metrics_counter


########################################################################################################################
