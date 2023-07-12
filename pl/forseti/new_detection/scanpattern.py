from collections import deque
from .tiles_manager import TilesManager
from rolling import PolynomialHash


def scanpattern(pattern: TilesManager, text: TilesManager, search_length: int, max_matches, compare_token_fun):
    longest_match = 0
    text_begin_idx = text.get_index_of_next_unmarked_token(0)

    if text_begin_idx is None or (text_begin_idx and text_begin_idx + search_length > text.size):
        return longest_match

    pattern_begin_idx = pattern.get_index_of_next_unmarked_token(0)

    if pattern_begin_idx is None or (pattern_begin_idx and pattern_begin_idx + search_length > pattern.size):
        return longest_match

    text_hash_to_positions = {}

    text_hasher = PolynomialHash([text.tokens[i].token_kind.short_name for i in range(text_begin_idx, text.size)], search_length)
    pattern_hasher = PolynomialHash([pattern.tokens[i].token_kind.short_name for i in range(pattern_begin_idx, pattern.size)], search_length)
    for i, current_hash in enumerate(text_hasher):
        text_idx = text_begin_idx + i
        marked_token_idx = text.get_index_of_next_marked_token(text_idx)

        # Skip tokens with at least 1 marks
        if marked_token_idx and marked_token_idx < text_idx + search_length:
            continue

        if current_hash not in text_hash_to_positions:
            text_hash_to_positions[current_hash] = []
        text_hash_to_positions[current_hash].append(text_idx)

    for i, current_hash in enumerate(pattern_hasher):
        pattern_idx = pattern_begin_idx + i

        marked_token_idx = pattern.get_index_of_next_marked_token(pattern_idx)

        # Skip tokens with at least 1 marks
        if marked_token_idx and marked_token_idx < pattern_idx + search_length:
            continue

        if pattern_hasher.current_value not in text_hash_to_positions:
            # Mismatch, skip
            continue

        for text_idx in text_hash_to_positions[pattern_hasher.current_value]:
            pattern_token_j = pattern_idx + search_length
            text_token_j = text_idx + search_length
            matching_tokens = search_length

            while (
                pattern_token_j < pattern.size
                and text_token_j < text.size
                and not pattern.marks[pattern_token_j]
                and not text.marks[text_token_j]
                and compare_token_fun(pattern.tokens[pattern_token_j], text.tokens[text_token_j])
            ):
                pattern_token_j += 1
                text_token_j += 1
                matching_tokens += 1

            if matching_tokens > 2 * search_length:
                # If match contains a lot of tokens there is probability that contains many smaller matches, taht are subset of it.
                # There is no point to continue, so return matches number and start with bigget search length.
                return matching_tokens

            if matching_tokens >= search_length:
                max_matches.append((pattern_idx, text_idx, matching_tokens))
                longest_match = max(longest_match, matching_tokens)

    return longest_match


def check_matches(matches, n1: int, n2: int) -> bool:
    """Checks, if matches are not overlaping.
    matches[0,1,2]: 0 pos of X token, 1 pos of Y token, 2 length of the match."""

    for match in matches:
        if (n1 >= match["position_of_token_1"] and n1 <= match["position_of_token_1"] + match["length"] - 1) or (
            n2 >= match["position_of_token_2"] and n2 <= match["position_of_token_2"] + match["length"] - 1
        ):
            return False
    return True


def mark_arrays(pattern: TilesManager, text: TilesManager, matches, compare_token_fun, tiles):
    length = 0

    for pattern_idx, text_idx, l in matches:
        is_match = all(
            [
                not all(pattern.marks[pattern_idx : pattern_idx + l]),
                not all(text.marks[text_idx : text_idx + l]),
                all([compare_token_fun(pattern.tokens[pattern_idx + i], text.tokens[text_idx + i]) for i in range(0, l)]),
            ]
        )
        if is_match:
            # Mark all tokens
            pattern.marks[pattern_idx : pattern_idx + l] = [True] * l
            text.marks[text_idx : text_idx + l] = [True] * l
            length += l
            # if check_matches(tiles, pattern_idx, text_idx):
            tiles.append({"position_of_token_1": pattern_idx, "position_of_token_2": text_idx, "length": l})

    return length
