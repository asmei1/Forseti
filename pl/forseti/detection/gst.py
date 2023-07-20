from operator import eq
from .tiles_manager import TilesManager
from .scanpattern import scanpattern, mark_arrays, check_matches


def gst(pattern: TilesManager, source: TilesManager, minimal_search_length: int, initial_search_length: int):
    search_length = initial_search_length
    tiles = []
    max_matches = []
    search_length_list = []
    max_iterations = 10
    counter = 0
    while counter < max_iterations:
        search_length_list.append(search_length)
        longest_match = scanpattern(pattern, source, search_length, max_matches)

        if longest_match > search_length * 2:
            # For very long matches restart detection to avoid subset matches
            search_length = longest_match
            continue

        mark_arrays(pattern, source, max_matches, tiles)
        max_matches = []
        if search_length > minimal_search_length * 2:
            search_length >>= 1
        elif search_length > initial_search_length:
            search_length = min(initial_search_length, min(pattern.size, source.size))
        else:
            break
        counter += 1

    filtered_tiles = []
    for tile in sorted(tiles, key=lambda x: x["length"], reverse=True):
        if tile["length"] < minimal_search_length:
            continue
        if check_matches(filtered_tiles, tile["position_of_token_1"], tile["position_of_token_2"]):
            filtered_tiles.append(tile)

    return filtered_tiles
