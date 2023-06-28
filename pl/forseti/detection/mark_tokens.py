from .tiles_manager import TilesManager
from .double_link_list import LinkedList


def mark_tokens(pattern: TilesManager, source: TilesManager, maximal_matches: LinkedList):
    for maximal_match_length in maximal_matches.maximal_matches:
        matches = maximal_matches.find(maximal_match_length).data
        maximal_matches.remove(maximal_match_length)
        for match in matches:
            for i in range(0, maximal_match_length):
                index_of_next_marked_token_in_pattern, index_of_next_marked_token_in_source = match
                pattern.set_mark(index_of_next_marked_token_in_pattern + i, mark=True)
                source.set_mark(index_of_next_marked_token_in_source + i, mark=True)
