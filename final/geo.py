#!/usr/bin/python3.8
# coding=utf-8
import pandas as pd
import geopandas
import matplotlib.pyplot as plt
import contextily
import sklearn.cluster
import numpy as np
# muzeze pridat vlastni knihovny



def make_geo(df: pd.DataFrame) -> geopandas.GeoDataFrame:
    """ Konvertovani dataframe do geopandas.GeoDataFrame se spravnym kodovani"""
    # drop NaNs in coordination columns
    df.dropna(subset= ["d"], inplace=True)
    df.dropna(subset= ["e"], inplace=True)
    # create GeoDataFrame
    gdf = geopandas.GeoDataFrame(df, geometry=geopandas.points_from_xy(df['d'], df['e']), crs="EPSG:5514")
    return gdf


def plot_geo(gdf: geopandas.GeoDataFrame, constrained_layout=True, fig_location: str = None,
             show_figure: bool = False):
    """ Vykresleni grafu s dvemi podgrafy podle lokality nehody """
    # do not show plot immediately
    plt.ioff()
    # plot two subplots side by side
    fig, ax = plt.subplots(1,2, constrained_layout=constrained_layout, figsize=(14,8))
    # do not plot axises
    ax[0].axis("off")
    ax[1].axis("off")
    # select only ZLK region
    gdf_zlk = gdf[gdf["region"] == "ZLK"]
    # convert projection
    gdf_zlk = gdf_zlk.to_crs(epsg=3857)
    # plot accidents
    gdf_zlk[gdf_zlk["p5a"] == 1].plot(ax=ax[0], markersize=6, color="tab:red", label="Nehody v obci")
    gdf_zlk[gdf_zlk["p5a"] == 2].plot(ax=ax[1], markersize=6, color="tab:green", label="Nehody mimo obec")
    # set titles
    ax[0].set_title('Nehody ve Zlinskem kraji: v obci')
    ax[1].set_title('Nehody ve Zlinskem kraji: mimo obec')
    # set map
    contextily.add_basemap(ax[0], crs=gdf_zlk.crs.to_string(), source=contextily.providers.Stamen.Toner, alpha=0.9)
    contextily.add_basemap(ax[1], crs=gdf_zlk.crs.to_string(), source=contextily.providers.Stamen.Toner, alpha=0.9)
    # save figure to fig_location
    if fig_location is not None:
        plt.savefig(fig_location)
    # show plot
    if show_figure:
        plt.show()


def plot_cluster(gdf: geopandas.GeoDataFrame, fig_location: str = None,
                 show_figure: bool = False):
    """ Vykresleni grafu s lokalitou vsech nehod v kraji shlukovanych do clusteru """
    # do not show plot immediately
    plt.ioff()
    
    # select JHC region
    gdf_c = gdf[gdf["region"] == "JHC"]
    # set geometry to centroid and convert projection
    gdf_c = gdf_c.set_geometry(gdf_c.centroid).to_crs(epsg=3857)
    # set coordinates
    coords = np.dstack([gdf_c.geometry.x, gdf_c.geometry.y]).reshape(-1, 2)
    # k-means to get clusters
    db = sklearn.cluster.MiniBatchKMeans(n_clusters=25).fit(coords)
    # create copy of gdc and insert column cluster
    gdf_jhc = gdf_c.copy()
    gdf_jhc["cluster"] = db.labels_
    # group gdf_jhc by cluster where accicents are counted
    gdf_jhc = gdf_jhc.dissolve(by="cluster", aggfunc={"p1": "count"}).rename(columns=dict(p1="cnt"))
    # get coordinates and merge with gdf_jhc
    gdf_coords = geopandas.GeoDataFrame(geometry=geopandas.points_from_xy(db.cluster_centers_[:, 0], db.cluster_centers_[:, 1]))
    gdf_points = gdf_jhc.merge(gdf_coords, left_on="cluster", right_index=True).set_geometry("geometry_y")

    # setup plot graph
    plt.figure(figsize=(20,10))
    ax = plt.gca()
    plt.axis("off")
    ax.set_title("Nehody ve zlinskem kraji")
    # plot result
    gdf_c.plot(ax=ax, color="tab:red", markersize=20, alpha=0.2)
    gdf_points.plot(ax=ax, markersize=gdf_points["cnt"]*2, column="cnt", legend=True, alpha=0.7)
    # add map as background
    contextily.add_basemap(ax, crs="epsg:3857", source=contextily.providers.Stamen.Toner, alpha=0.6)

    # save figure to fig_location if location is given
    if fig_location is not None:
        plt.savefig(fig_location)
    # show plot if requested
    if show_figure:
        plt.show()


if __name__ == "__main__":
    # zde muzete delat libovolne modifikace
    gdf = make_geo(pd.read_pickle("accidents.pkl.gz"))
    plot_geo(gdf, "geo1.png", True)
    plot_cluster(gdf, "geo2.png", True)

