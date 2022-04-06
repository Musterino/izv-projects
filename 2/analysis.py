#!/usr/bin/env python3.8
# coding=utf-8

from matplotlib import pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
import os
# muzete pridat libovolnou zakladni knihovnu ci knihovnu predstavenou na prednaskach
# dalsi knihovny pak na dotaz

# Ukol 1: nacteni dat
def get_dataframe(filename: str, verbose: bool = False) -> pd.DataFrame:
    # check if file exists
    if os.path.exists(filename) and os.path.isfile(filename):
        # create dataframe and fill it
        df = pd.read_pickle(filename)
        if verbose:
            # print original dataframe size
            print(f'orig_size={np.round(df.memory_usage(deep=True).sum() / 1048576, 1)} MB')
        # go through every series of dataframe and 
        for col_name, col_data in df.iteritems():
            # column is int
            if df[col_name].dtype == np.int32:
                # check if max value in column can be byte
                if df[col_name].max() < 128 and df[col_name].min() > -128:
                    # set dtype of column to int8 for memory savings
                    df[col_name] = df[col_name].astype("int8")
            # column is region, don't change anything
            elif col_name == "region":
                pass
            # column is type object
            elif df[col_name].dtype == np.object:
                # make it category for memory savings
                df[col_name] = df[col_name].astype('category')
        # create date column
        df["date"] = df["p2a"]
        df["date"] = df["date"].astype(np.datetime64)
        if verbose:
            # print changed dataframe size
            print(f'new_size={np.round(df.memory_usage(deep=True).sum() / 1048576, 1)} MB')
        # return data
        return df

# Ukol 2: následky nehod v jednotlivých regionech
def plot_conseq(df: pd.DataFrame, fig_location: str = None,
                show_figure: bool = False):
    # turn off interactive mode
    plt.ioff()
    # setup 4 subplots in 1 column
    fig, axes = plt.subplots(4,1, constrained_layout=True, figsize=(10,10))
    fig.suptitle("Následky nehod v jednotlivých regionech")
    
    sns.set_theme()

    # get sums of entries at which someone passed away
    df_agg_a = df.groupby(["region"]).agg({"p13a": "sum"})
    df_agg_a.reset_index(inplace=True)
    # plot it
    sns.barplot(ax=axes[0], x="region", y="p13a", data=df_agg_a.sort_values("p13a", ascending=False), palette="Reds_r")
    # set titles
    axes[0].set_title("Počet úmrtí při nehodách")
    axes[0].set_xlabel("Regiony")
    axes[0].set_ylabel("Počet úmrtí")

    # get sums of entries at which someone was severely injured
    df_agg_b = df.groupby(["region"]).agg({"p13b": "sum"})
    df_agg_b.reset_index(inplace=True)
    sns.barplot(ax=axes[1], x="region", y="p13b", data=df_agg_b.sort_values("p13b", ascending=False), palette="Reds_r")
    # set titles
    axes[1].set_title("Počet těžce zraněných")
    axes[1].set_xlabel("Regiony")
    axes[1].set_ylabel("Počet zraněných")

    # get sums of entries at which someone was slightly injured
    df_agg_c = df.groupby(["region"]).agg({"p13c": "sum"})
    df_agg_c.reset_index(inplace=True)
    sns.barplot(ax=axes[2], x="region", y="p13c", data=df_agg_c.sort_values("p13c", ascending=False), palette="Reds_r")
    # set titles
    axes[2].set_title("Počet lehce zraněných")
    axes[2].set_xlabel("Regiony")
    axes[2].set_ylabel("Počet zraněných")

    # plot count of all accidents
    sns.countplot(ax=axes[3], x="region", data=df, order=df["region"].value_counts().index, palette="Reds_r")
    # set titles
    axes[3].set_title("Celkový počet nehod")
    axes[3].set_xlabel("Regiony")
    axes[3].set_ylabel("Počet nehod")

    # save figure to fig_location
    plt.savefig(fig_location)

    # show figure if requested
    if show_figure:
        plt.show()


# Ukol3: příčina nehody a škoda
def plot_damage(df: pd.DataFrame, fig_location: str = None,
                show_figure: bool = False):
    pass

# Ukol 4: povrch vozovky
def plot_surface(df: pd.DataFrame, fig_location: str = None,
                 show_figure: bool = False):
    pass


if __name__ == "__main__":
    pass
    # zde je ukazka pouziti, tuto cast muzete modifikovat podle libosti
    # skript nebude pri testovani pousten primo, ale budou volany konkreni ¨
    # funkce.
    df = get_dataframe("accidents.pkl.gz")
    plot_conseq(df, fig_location="01_nasledky.png", show_figure=True)
    plot_damage(df, "02_priciny.png", True)
    plot_surface(df, "03_stav.png", True)
