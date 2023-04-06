import logging
import os
import fnmatch

def validate_file_paths(paths): 
    for file_paths in paths:
        for path in file_paths:
            if not os.path.exists(path) or not os.path.isfile(path):
                raise FileNotFoundError(path)


def scan_for_files(paths, patterns):
    scanned_paths = []
    if len(paths) >= 2:
        logging.info('Passing multiple programs explicitly')
        scanned_paths = paths
    elif len(paths) == 1 and len(paths[0]) == 1 and os.path.isdir(paths[0][0]):
        logging.info('Passing folder with sources')
        
        for file_entry in os.listdir(paths[0][0]):
            if not os.path.isdir(os.path.join(paths[0][0], file_entry)):
                file_path = file_entry
                for pattern in tuple(patterns):
                    for file in fnmatch.filter([file_path], pattern):
                        scanned_paths.append([os.path.abspath(os.path.join(paths[0][0], file))])
                        
            else:
                folder = os.path.join(paths[0][0], file_entry)
                canditate_files = [f for f in os.listdir(folder)]
                files = []
                for pattern in tuple(patterns):
                    for file in fnmatch.filter(canditate_files, pattern):
                        files.append(os.path.abspath(os.path.join(folder, file)))
                if files:
                    scanned_paths.append(files)
                else:
                    logging.warning('Folder %s does not have any source code files', folder)
    
    validate_file_paths(scanned_paths)
    return scanned_paths
        
