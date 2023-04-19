import dataclasses
import multiprocessing

@dataclasses.dataclass
class DetectionConfig:
    unroll_ast: bool = True
    remove_unrolled_function: bool = True
    unroll_only_simple_functions: bool = True
    compare_whole_program: bool = False
    assign_functions_based_on_types: bool = True
    max_number_of_differences_in_single_comparison_pair: int = -1
    minimal_search_length: int = 8
    initial_search_length: int = 20 
    compare_function_names_in_function_calls: bool = True  
    distinguish_operators_symbols: bool = True  
    n_processors: int = 1

