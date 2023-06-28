import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def generate_heatmap(df: pd.DataFrame, title: str):
    plot_width, plot_height = plt.rcParams["figure.figsize"]

    # Turn interactive plotting off
    plt.ioff()
    mask = np.triu(np.ones_like(df.values, dtype=bool))

    heatmap = sns.heatmap(df, annot=True, mask=mask, xticklabels=True, yticklabels=True, vmin=0, vmax=1)
    figure = heatmap.get_figure()
    scale_factor = df.values.shape[0] / 4
    scale_factor = scale_factor if scale_factor > 1 else 1
    figure.set_size_inches(plot_width * scale_factor, plot_height * scale_factor)
    figure.suptitle(title, fontsize=20)
    figure.tight_layout()
    return figure
