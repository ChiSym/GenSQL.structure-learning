import json
import pandas as pd
from sppl.compilers.spe_to_dict import spe_from_dict
from sppl.transforms import Id
from sppl.spe import Memo
from itertools import product
from tqdm import tqdm
import numpy as np
import edn_format
import altair as alt
import scipy.interpolate
from statsmodels.nonparametric.smoothers_lowess import lowess as sm_lowess
from functools import reduce


def smooth(x, y, xgrid, divide=2):
    samples = np.random.choice(len(x), len(x) // divide, replace=False)
    y_s = y[samples]
    x_s = x[samples]
    y_sm = sm_lowess(y_s, x_s, frac=0.5, it=5, return_sorted=False)
    # regularly sample it onto the grid
    y_grid = scipy.interpolate.interp1d(x_s, y_sm, fill_value="extrapolate")(xgrid)
    return y_grid


with open("data/sppl/merged.json", "rb") as f:
    metadata = json.load(f)
    spe = spe_from_dict(metadata)

n_models = len(spe.children)

with open("data/mapping-table.edn", "rb") as f:
    mapping_table = edn_format.loads(f.read())

# sample prostate_specific_antigen values for different treatments and days

days = np.arange(0, 100, 10)
treatments = ["Placebo", "Docetaxel"]

real_df = pd.read_csv("data/subsampled.csv")
filtered_df = real_df[
    (real_df["Treatment"].isin(["Placebo", "Docetaxel"]))
    & (real_df["Race"] == "Black")
    & (real_df["Age"] >= 30)
    & (real_df["Age"] <= 40)
    & (real_df["Day"] >= 0)
    & (real_df["Day"] <= 90)
]

dfs = []

K = 100
# child_spe = spe.constrain({
#     Id("Age"): 30,
#     Id("Race"): "Black"})

child_spe = spe.constrain({Id("Age"): 30})

days = np.arange(0, 100, 10)

for treatment in treatments:
    treatment_spe = child_spe.constrain({Id("Treatment"): treatment})
    for day in tqdm(days):
        day_spe = treatment_spe.constrain({Id("Day"): day})
        samples = day_spe.sample(1000)
        psa = [s[Id("Prostate_Specific_Antigen")] for s in samples]
        # day = [s[Id("Day")] for s in samples]

        df = pd.DataFrame(
            {
                "Prostate_Specific_Antigen": psa,
                "Treatment": treatment,
                "Day": day,
            }
        )

        dfs.append(df)

df = pd.concat(dfs)

placebo_df = df[df["Treatment"] == "Placebo"]
docetaxel_df = df[df["Treatment"] == "Docetaxel"]


def make_fig(df, divide=2):
    x = df["Day"].to_numpy()
    y = df["Prostate_Specific_Antigen"].to_numpy()
    xgrid = np.linspace(0, 90)
    K = 100
    return np.stack([smooth(x, y, xgrid, divide) for k in tqdm(range(K))]).T
    # plt.savefig("ate_loess.png")


placebo_smooths = make_fig(placebo_df, divide=1)
docetaxel_smooths = make_fig(docetaxel_df, divide=1)

placebo_many_smooths = make_fig(placebo_df, divide=2)
docetaxel_many_smooths = make_fig(docetaxel_df, divide=2)

placebo_many_smooths -= placebo_smooths[1]
docetaxel_many_smooths -= docetaxel_smooths[1]

placebo_smooths -= placebo_smooths[1]
docetaxel_smooths -= docetaxel_smooths[1]

xgrid = np.linspace(0, 90)
placebo_df = pd.DataFrame(
    {
        "Treatment": "Placebo",
        "psa": placebo_smooths[:, 0],
        "days": xgrid,
    }
)
docetaxel_df = pd.DataFrame(
    {
        "Treatment": "Docetaxel",
        "psa": docetaxel_smooths[:, 0],
        "days": xgrid,
    }
)

results_df = []
for i in range(100):
    placebo_df = pd.DataFrame(
        {
            "Treatment": "Placebo",
            "psa": placebo_many_smooths[:, i],
            "days": xgrid,
            "run": i,
        }
    )
    docetaxel_df = pd.DataFrame(
        {
            "Treatment": "Docetaxel",
            "psa": docetaxel_many_smooths[:, i],
            "days": xgrid,
            "run": i,
        }
    )
    results_df.append(placebo_df)
    results_df.append(docetaxel_df)


main_df = pd.concat([placebo_df, docetaxel_df])
lines_df = pd.concat(results_df)

line = (
    alt.Chart(main_df)
    .mark_line(strokeWidth=5)
    .encode(
        x=alt.X(
            "days:Q",
            title="Days since treatment start",
            scale=alt.Scale(domain=[0, 90]),
        ),
        y=alt.Y("psa:Q", scale=alt.Scale(domain=[-30, 100])),
        color="Treatment:N",
    )
)


def make_lines_chart(run, treatment):
    df = lines_df[lines_df["run"] == run]
    df = df[df["Treatment"] == treatment]
    color = alt.Color(
        "Treatment:N",
        scale=alt.Scale(domain=["Placebo", "Docetaxel"], range=["orange", "blue"]),
    )
    lines = (
        alt.Chart(df)
        .mark_line(opacity=0.1)
        .encode(
            x=alt.X(
                "days:Q",
                title="Days since treatment start",
                scale=alt.Scale(domain=[0, 90]),
            ),
            y=alt.Y("psa:Q").scale(zero=False),
            color=color,
        )
    )
    return lines


placebo_lines = [make_lines_chart(i, "Placebo") for i in range(K)]
placebo_plot = reduce(lambda x, y: x + y, placebo_lines)
docetaxel_lines = [make_lines_chart(i, "Docetaxel") for i in range(K)]
docetaxel_plot = reduce(lambda x, y: x + y, docetaxel_lines)

plot = (placebo_plot + docetaxel_plot + line).configure_axisY(
    titleAngle=0,
    title=[
        "Change in",
        "Prostate-specific antigen",
    ],
)

plot.save("30_yo_average_treatment_effect.png")

import ipdb

ipdb.set_trace()
