from multiprocessing import Pool
import tqdm


def execute_function_in_multiprocesses(func, data, n_processors, mininterval=0.1, chunksize=1):
    with Pool(processes=n_processors) as pool:
        return list(tqdm.tqdm(pool.imap_unordered(func, data, chunksize=chunksize), total=len(data), mininterval=mininterval))
