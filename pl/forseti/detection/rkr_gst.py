from operator import eq
from typing import List
from .tiles_manager import TilesManager
from .double_link_list import LinkedList
from .scanpattern import scanpattern
from .mark_tokens import mark_tokens

def check_matches(matches,  n1: int, n2: int) -> bool:
    """Checks, if matches are not overlaping.
    matches[0,1,2]: 0 pos of X token, 1 pos of Y token, 2 length of the match."""

    for match in matches:
        if (n1 >= match['position_of_token_1'] and n1 <= match['position_of_token_1'] + match['length'] - 1) or (
                n2 >= match['position_of_token_2'] and n2 <= match['position_of_token_2'] + match['length'] - 1):
            return False
    return True

def rkr_gst(pattern: TilesManager, source: TilesManager, minimal_search_length:int, initial_search_length:int, subsequence_generator_function = "".join, token_comparision_function = eq):
    search_length = initial_search_length
    all_matches = []
    while True:
        maximal_matches = LinkedList()
        longest_maximal_match = scanpattern(pattern, source, search_length, maximal_matches, subsequence_generator_function, token_comparision_function)

        if longest_maximal_match > 2 * search_length:
            search_length = longest_maximal_match
        else:
            mark_tokens(pattern, source, maximal_matches)


            for maximal_match_length in maximal_matches.maximal_matches:
                if maximal_match_length < search_length:
                    continue
                queue = maximal_matches.find(maximal_match_length)
                if queue:
                    matches = queue.data
                    for m in matches:
                        if not check_matches(all_matches, m[0], m[1]):
                            continue

                        all_matches.append(
                            {
                                'position_of_token_1': m[0],
                                'position_of_token_2': m[1],
                                'length': maximal_match_length,
                            })
                        

            if search_length > 2 * minimal_search_length:
                search_length = int(search_length / 2) + 1
            elif search_length > minimal_search_length:
                search_length = minimal_search_length
            else:
                break
    if all_matches:
        all_matches = sorted(all_matches, key=lambda x: x['length'], reverse=True)
    return all_matches if all_matches else None