from multiprocessing import Pool
from multiprocessing import freeze_support


def execute_function_in_multiprocesses(func, data, n_processors):
    with Pool(processes=n_processors) as pool:
        return pool.map(func, data)
