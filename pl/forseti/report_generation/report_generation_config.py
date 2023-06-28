from dataclasses import dataclass


@dataclass
class ReportGenerationConfig:
    generate_heatmap_for_whole_programs: bool = False
    generate_heatmap_for_code_units: bool = False
    generate_jsons: bool = True
    generate_html_diffs: bool = True
    generate_code_unit_metrics: bool = True
    n_processors: int = 1
    assign_functions_based_on_types: bool = True
    output_path: str = ""
