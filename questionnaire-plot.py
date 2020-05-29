#!/usr/bin/env python3
import click
import pandas as pd
import sys
import matplotlib.pyplot as plt
import os
import numpy as np
from scipy.stats import gaussian_kde

def csv_to_pandas(csvfile):
    """Returns two dataframes, one containing the average
    amount of time spent per sheet, one containing the 
    perceived difficulty"""
    df = pd.read_csv(csvfile, skiprows=[0], index_col=0)
    return df.iloc[:, :6], df.iloc[:, 7:]

def make_plots(csvfile, sheet):
    time, difficulty = csv_to_pandas(csvfile)

    # average time spent for exercise in each category
    time_weighting = [1.5, 3.5, 5.5, 8, 12, 17] 

    # setting up for saving
    outdir = os.path.join(os.path.dirname(csvfile), f"sheet_{sheet:02d}")
    os.mkdir(outdir)
    outpath = lambda f: os.path.join(outdir, f)
    save = lambda f: plt.savefig(outpath(f))

    # time plots
    bins = [2, 4, 6, 9, 14, 17.5]
    make_time_hist(time, time_weighting, bins, sheet)
    save(f"bar_time_sheet{sheet:02d}")

    # difficulty plots
    make_difficulty_bar(difficulty, sheet)
    save(f"bar_difficulty_sheet{sheet:02d}")

    # getting stats
    report_stats(time, time_weighting, difficulty, sheet, outpath(f"report_sheet{sheet:02d}.txt"))

    
def report_stats(time, time_weighting, difficulty, sheet, outfile):
    time = time.loc[sheet]
    difficulty = difficulty.loc[sheet]

    mean   = f"Durchschnittlicher Zeitaufwand: {calc_mean_weighting(time, time_weighting):.2f}\n"

    diff_num, diff_desc = difficulty.values[difficulty.argmax()], difficulty.index[difficulty.argmax()]
    diff_level = f"Die meisten Studenten empfanden das Blatt als {diff_desc} ({diff_num} Studenten)"

    with open(outfile, "w+") as f:
        f.writelines([mean, diff_level])
    

def calc_mean_weighting(array, weighting):
    if len(array) != len(weighting):
        raise ValueError(f"Length of array {len(arrray)} != length of weighting {len_weighting}")
    mean = 0
    for count, weight in zip(array, weighting):
        mean += count * weight
    return mean/sum(array)

def make_time_hist(time, weighting, bins, sheet, plot_kde=True):
    """ We need some weird workarounds here..."""
    time = time.loc[sheet]
    plt.figure()
    hist_array = []
    for count, weight in zip(time, weighting):
        hist_array += [weight] * count
    plt.hist(hist_array, bins=bins, label="Time spent")
    if plot_kde:
        ker = gaussian_kde(hist_array)
        x = np.linspace(min(bins) - 1, max(bins) + 1)
        y = ker.evaluate(x)
        plt.plot(x, y / max(y) * max(time), label="KDE")
    mean = calc_mean_weighting(time, weighting)
    plt.axvline(mean, 0, max(time) + 1, linestyle='dashed', label="Mean", c="black")
    plt.title(f"Histogram of time spent on exercise sheet {sheet}, mean = {mean:.2f}")
    plt.legend()
    

def make_difficulty_bar(df, sheet):
    plt.figure()
    series = df.loc[sheet]
    labels, vals = series.index, series.values
    plt.bar(labels, vals)
    plt.title(f"Perceived difficulty of sheet {sheet}")


@click.argument("data-file", type=click.Path(exists=True), required=True)
@click.option("-s", "--sheet", type=int, prompt="Enter the number of the current sheet",
              help="Number of the current sheet.")
@click.command()
def cli(data_file, sheet):
    if not data_file.endswith("csv"):
        raise ValueError(f"Given file {file} was not a zip file.")
    make_plots(data_file, sheet) 

if __name__ == "__main__":
    cli() 
