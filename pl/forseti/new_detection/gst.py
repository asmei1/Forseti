from operator import eq
from .tiles_manager import TilesManager
from .scanpattern import scanpattern, mark_arrays, check_matches


def gst(pattern: TilesManager, source: TilesManager, minimal_search_length: int, initial_search_length: int, compare_token_fun):
    search_length = initial_search_length
    tiles = []
    max_matches = []
    search_length_list = []

    while search_length not in search_length_list:
        search_length_list.append(search_length)
        longest_match = scanpattern(pattern, source, search_length, max_matches, compare_token_fun)

        if longest_match > search_length * 2:
            # For very long matches restart detection to avoid subset matches
            search_length = longest_match
            continue

        mark_arrays(pattern, source, max_matches, compare_token_fun, tiles)
        max_matches = []
        if search_length > minimal_search_length * 2:
            search_length >>= 1
        elif search_length > initial_search_length:
            search_length = min(initial_search_length, min(pattern.size, source.size))
        else:
            break

    filtered_tiles = []
    for tile in sorted(tiles, key=lambda x: x["length"], reverse=True):
        if tile["length"] < minimal_search_length:
            continue
        filtered_tiles.append(tile)

    return filtered_tiles
