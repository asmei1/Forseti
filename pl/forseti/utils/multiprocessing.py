from multiprocessing import Pool
import tqdm


def execute_function_in_multiprocesses(func, data, n_processors):
    with Pool(processes=n_processors) as pool:
        return list(tqdm.tqdm(pool.imap(func, data), total=len(data)))
