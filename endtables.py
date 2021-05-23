# collect all final tables for the first 3 leagues since 1990. along with individual ranks
# compute a score (Bundesliga: 1-18, 2. Bundesliga 19-36, 3.Bundesliga 37-40, all other 40.

from itertools import product
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from bokeh.plotting import figure
from bokeh.io import output_file, show
from bokeh.models import Range1d, HoverTool

discount_faktor = 0.04

TEAM_HIGHLIGHT = "SC Freiburg"


def collect():
    """ Crawls through the final tables of each season.
    """
    tables = pd.DataFrame(columns=["liga", "season", "rank", "team"])

    for liga in [1, 2, 3]:
        if liga == 3:
            firstyear = 2008
        else:
            firstyear = 1993
        for s in list(range(firstyear, 2020)):
            if (
                (liga == 3)
                or ((liga == 1) and (s == 1991))
                or ((liga == 2) and (s == 1993))
            ):
                m = 38
            else:
                m = 34

            html = open(
                "data/league_{}/raw/kicker_{}_{}.html".format(liga, s, m),
                "r",
                encoding="utf-8",
            ).read()

            clubs = re.findall('class="link verinsLinkBild" style="">(.+?)</a>', html)

            onetable = pd.DataFrame(
                {
                    "liga": [liga] * len(clubs),
                    "season": [s] * len(clubs),
                    "rank": list(range(1, len(clubs) + 1)),
                    "team": clubs,
                }
            )

            tables = tables.append(onetable)

    return tables


df = collect()
# Clean Team Names
for pat in [
    r" \*",
    r" \(A\)",
    r" \(M\)",
    r" \(P\)",
    r" \(M, P\)",
    r" \(N\)",
    r" \(P, A\)",
]:
    df["team"] = df["team"].str.replace(pat, "")

df["season"] = df["season"].astype(int)
# keep only teams which played at least 2. bundesliga
df = df.join(df.groupby("team")["liga"].min(), on="team", how="left", rsuffix="_min")
df = df[df["liga_min"] <= 2]

# fill teams+years for missing years and assign them a score of 40.
comb = pd.DataFrame(
    list(product(df["team"].unique(), df["season"].unique())),
    columns=["team", "season"],
)

df = df.merge(comb, on=["team", "season"], how="outer")

# assign score. use some kind of discount to value current values higher
df.loc[df["rank"].isna(), "score"] = 40
df.loc[df["liga"] == 1, "score"] = df["rank"]
df.loc[df["liga"] == 2, "score"] = df["rank"] + 18
df.loc[df["liga"] == 3, "score"] = np.minimum(40, df["rank"] + 36)
assert ~df["score"].isna().any()


df["discount"] = (1 - discount_faktor) ** (df["season"].max() - df["season"])
df["score_disc"] = df["score"] * df["discount"]
out = pd.DataFrame(df.groupby("team")["score_disc"].sum().sort_values())
out = out.reset_index()

# visualize it...with matplotlib
titlestring = "Discounted Rank, {}/{}-{}/{}".format(
    df["season"].min(),
    (df["season"].min() + 1) % 100,
    df["season"].max(),
    (df["season"].max() + 1) % 100,
)
filename = "buli_since{}".format(df["season"].min())

fig = plt.figure(figsize=(11, 15))
ax = fig.add_subplot(111)
fig.subplots_adjust(left=0.3)
bars = ax.barh(
    out["team"],
    out["score_disc"].max() - out["score_disc"],
    left=out["score_disc"],
    height=0.7,
)

bars[out[out["team"] == TEAM_HIGHLIGHT].index.tolist()[0]].set_color("orange")
ax.invert_xaxis()
ax.invert_yaxis()
# plt.yticks(np.multiply(list(range(len(out))),1.2), out.index)
for bar in bars:
    bar.sticky_edges.x[:] = [out["score_disc"].max()]
ax.autoscale()
ax.tick_params(labelsize=12)
plt.title(titlestring)
plt.savefig("{}.png".format(filename))

# Now Try the same thing with bokeh
for graph in [filename, "{}_top20".format(filename)]:
    output_file("{}.html".format(graph))
    if graph == "{}_top20".format(filename):
        out = out[:20]

    p = figure(x_range=out["team"], plot_height=500, plot_width=1000, title=titlestring)
    colorlist = np.select(
        [out["team"] != TEAM_HIGHLIGHT, out["team"] == TEAM_HIGHLIGHT],
        ["blue", "orange"],
    )

    p.vbar(
        x=out["team"],
        top=out["score_disc"],
        bottom=out["score_disc"].max() * 1.03,
        color=colorlist,
        width=0.5,
    )

    p.xaxis.major_label_orientation = "vertical"
    # Set some properties to make the plot look better
    p.xgrid.grid_line_color = None
    p.y_range.range_padding = 0.1
    p.y_range = Range1d(out["score_disc"].max() * 1.03, 0)

    show(p)
