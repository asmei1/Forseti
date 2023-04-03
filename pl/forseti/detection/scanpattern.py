from typing import List
from .tiles_manager import TilesManager
from .double_link_list import LinkedList
from .hashtable import Hashtable

def scanpattern(pattern: TilesManager, source: TilesManager, search_length:int, maximal_matches:LinkedList, subsequence_generator_function, token_comparision_function):
    hashtable = Hashtable()

    index_of_next_unmarked_token = pattern.get_index_of_next_unmarked_token(0)
    distance_to_next_tile = 0
    while index_of_next_unmarked_token is not None:
        index_of_next_marked_token = pattern.get_index_of_next_marked_token(index_of_next_unmarked_token)

        if not index_of_next_marked_token:
            distance_to_next_tile = pattern.size() - index_of_next_unmarked_token
        else:
            distance_to_next_tile = (index_of_next_marked_token + 1) - index_of_next_unmarked_token

        if distance_to_next_tile < search_length:
            if index_of_next_marked_token:
                index_of_next_unmarked_token = pattern.get_index_of_next_unmarked_token(index_of_next_marked_token)
            else:
                index_of_next_unmarked_token = None
        else:
            #Found substring
            unmarked_token_start_index = index_of_next_unmarked_token
            unmarked_token_end_index = index_of_next_unmarked_token + search_length
            sequence = subsequence_generator_function(pattern.tokens[unmarked_token_start_index:unmarked_token_end_index])
            hash_value = hashtable.create_hash(sequence)
            data = (unmarked_token_start_index, unmarked_token_end_index - 1)
            hashtable.add(hash_value, data)

            index_of_next_unmarked_token = pattern.get_index_of_next_unmarked_token(index_of_next_unmarked_token + 1)

    longest_maximal_match = 0

    index_of_next_unmarked_token = source.get_index_of_next_unmarked_token(0)
    while index_of_next_unmarked_token is not None:
        index_of_next_marked_token = source.get_index_of_next_marked_token(index_of_next_unmarked_token)

        if not index_of_next_marked_token:
            distance_to_next_tile = source.size() - index_of_next_unmarked_token
        else:
            distance_to_next_tile = (index_of_next_marked_token + 1) - index_of_next_unmarked_token

        if distance_to_next_tile < search_length:
            if index_of_next_marked_token:
                index_of_next_unmarked_token = source.get_index_of_next_unmarked_token(index_of_next_marked_token)
            else:
                index_of_next_unmarked_token = None
        else:
            # Found a sequence to calculate hash  
            
            unmarked_token_start_index = index_of_next_unmarked_token
            unmarked_token_end_index = index_of_next_unmarked_token + search_length

            sequence = subsequence_generator_function(source.tokens[unmarked_token_start_index:unmarked_token_end_index])
            created_hash = hashtable.create_hash(sequence)
            values = hashtable.get(created_hash)

            k = 0
            for value in values:
                m = value[0]
                source_token = pattern.tokens[m + k]
                pattern_token = source.tokens[unmarked_token_start_index + k]
                is_unmarked_source_token = not pattern.is_marked(m + k)
                is_unmarked_pattern_token = not source.is_marked(unmarked_token_start_index + k)
                while token_comparision_function(source_token, pattern_token) \
                    and (is_unmarked_source_token and is_unmarked_pattern_token) \
                    and (m + k <= pattern.size() - 1) \
                    and (unmarked_token_start_index + k <= source.size() - 1):

                    # If at end of tokens allow increment because there was a match.
                    k += 1 
                    if k > search_length * 2:
                        # Abandon the scan. It will be restarted with search_length = k.
                        return k
                
                    if m + k != pattern.size() and unmarked_token_start_index + k != source.size():
                        pattern_token = pattern.tokens[m + k]
                        source_token = source.tokens[unmarked_token_start_index + k]
                        is_unmarked_pattern_token = not pattern.is_marked(m + k)
                        is_unmarked_source_token = not source.is_marked(unmarked_token_start_index + k)
                    else:
                        break
                maximal_matches.add(k, (m, unmarked_token_start_index))

            if k > longest_maximal_match:
                longest_maximal_match = k
            
            index_of_next_unmarked_token = source.get_index_of_next_unmarked_token(index_of_next_unmarked_token + 1)

    return longest_maximal_match
