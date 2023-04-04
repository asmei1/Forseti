import dataclasses
import multiprocessing

@dataclasses.dataclass
class DetectionConfig:
    unroll_ast: bool = True
    remove_unrolled_function: bool = True
    unroll_only_simple_functions: bool = True
    compare_whole_program: bool = False
    assign_functions_based_on_types: bool = True
    max_number_of_differences_in_single_submission: int = 15
    n_processors: int = multiprocessing.cpu_count() - 1 if multiprocessing.cpu_count() - 1 else 1

