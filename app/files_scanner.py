import logging
import os

def dir_path(self, optional_path):
    """
    Checks, if given path is directory.
    If not, raise NotADirectoryError
    """

    if os.path.isdir(optional_path):
        return optional_path
    else:
        raise NotADirectoryError(optional_path)

def validate_file_paths(paths): 
    for file_paths in paths:
        for path in file_paths:
            if not os.path.exists(path) or not os.path.isfile(path):
                raise FileNotFoundError(path)



def scan_for_files(paths, extensions):
    scanned_paths = []
    if len(paths) >= 2:
        logging.info('Passing multiple programs explicitly')
        scanned_paths = paths
    elif len(paths) == 1 and len(paths[0]) == 1 and os.path.isdir(paths[0][0]):
        logging.info('Passing folder with sources')
        
        for folder in os.listdir(paths[0][0]):
            folder = os.path.join(paths[0][0], folder)
            if not os.path.isdir(folder):
                continue
            files = []
            for file in os.listdir(folder):
                file = os.path.abspath(os.path.join(folder, file))
                if os.path.splitext(file)[1] in extensions:
                    files.append(file)
                else:
                    logging.warning('Detected not valid file: %s. Skipped', file)
            if files:
                scanned_paths.append(files)
            else:
                logging.warning('Folder %s does not have any source code files', folder)
    
    validate_file_paths(scanned_paths)
    return scanned_paths
        
