
from factorizations import CFL
from factorizations import ICFL_recursive
from factorizations import CFL_icfl
from factorizations_comb import d_cfl
from factorizations_comb import d_icfl
from factorizations_comb import d_cfl_icfl

import pickle


# Split long reads in subreads
def factors_string(string='', size=300):
    list_of_factors = []

    if len(string) < size:
        list_of_factors.append(string)
    else:
        # print('len(string): ', len(string))
        for i in range(0, len(string), size):
            # print("i: ", i)
            if i + size > len(string):
                fact = string[i:len(string)]
            else:
                fact = string[i:i + size]

            list_of_factors.append(fact)

    return list_of_factors


def compute_fingerprint(sequence='', split=300, type_factorization='CFL',fact_file='no_create'):


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

    list_of_factors = factors_string(sequence, size=split)

    fingerprint = ''
    l_factorization = ''
    for i in range(len(list_of_factors)):
        sft = list_of_factors[i]
        print(len(sft))

        list_fact = factorization(sft, T)

        # Remove special characters
        if '>>' in list_fact:
            list_fact[:] = (value for value in list_fact if value != '>>')
        if '<<' in list_fact:
            list_fact[:] = (value for value in list_fact if value != '<<')

        fingerprint = fingerprint + ' '.join(str(len(fact)) for fact in list_fact)

        if fact_file == 'create':
            l_factorization = l_factorization + ' '.join(fact for fact in list_fact)

        #if i > 0:
        fingerprint += ' | '
        if fact_file == 'create':
            l_factorization += ' | '

    if fact_file == 'create':
        return [fingerprint, l_factorization]
    else:
        return fingerprint


def xxx():

    list_cfl = ['aaaavxfs',
                'gdhgdtaf',
                'agagdgag',
                'adav',
                'agdgdagagdgagdagdgagdg',
                'adgabch']

    l_prefix = 20
    l_distance = 10

    current_p = ''
    current_i = 0
    last_i = 0
    start_fact = 0
    for i, fact in enumerate(list_cfl):
        current_p += fact

        if len(current_p) > l_prefix:
            current_pref = current_p[:l_prefix]

            current_distance = 0
            l_1 = 0
            list_1 = list_cfl[:start_fact]
            for f in list_1:
                l_1 += len(f)

            l_2 = 0
            list_2 = list_cfl[:last_i]
            for f in list_2:
                l_2 += len(f)

            current_distance = l_1 - l_2
            # print('current distance: {}'.format(current_distance))

            if last_i == 0 or current_distance > l_distance:
                # print('current distance: {}'.format(current_distance))
                try:
                    # search for the item
                    print(current_pref)
                except ValueError:
                    # print('update dictionary: {}'.format(current_p))
                    print(current_pref)

                last_i = start_fact

                start_fact = i + 1
                current_i = i + 1
                current_p = ''
        else:
            current_i = i + 1

if __name__ == '__main__':

    w = 'above for $RR$.  $SS$ might be a bounded set of integers or some more complex'
    #w = 'ciao'
    lst = ICFL_recursive(w,10)
    print(lst)
