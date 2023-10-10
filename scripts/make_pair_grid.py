import pandas as pd
import altair as alt
import numpy as np

real_data_path = "data/data.csv"

df = pd.read_csv(real_data_path)
numerics = ["int16", "int32", "int64", "float16", "float32", "float64"]

df = df.select_dtypes(exclude=numerics).sample(1000)

# cols_to_filter = ["Creatinine", "Sodium"]
# cols_to_filter = ["Sodium", "Blood_Urea_Nitrogen"]
# cols_to_filter = [c for c in dfs[0].select_dtypes([np.number]).columns]

# lpm_df = full_df[full_df["source"].isin(["Real", "LPM"])]
# ctgan_df = full_df[full_df["source"].isin(["Real", "CTGAN"])]
# copula_df = full_df[full_df["source"].isin(["Real", "Copula"])]
# real_df = full_df[full_df["source"].isin(["Real"])]

# models = ["Real", "LPM", "CTGAN", "Copula"]

# filtered_dfs = [full_df[full_df["source"].isin([model])] for model in models]
df = df[df.isna().sum().sort_values().keys()]
columns = list(df.columns)[:10]
rows = columns[:10]

# df = df.dropna(axis=0, subset=columns)


# chart = alt.Chart(df).mark_rect().encode(
#     alt.X(alt.repeat("repeat"), type='nominal').axis(labels=False, labelLimit=0),
#     alt.Y("newsint:N", axis=alt.Axis(labels=False)),
#     color=alt.Color("count():Q", legend=None),
# ).properties(
#     width=150,
#     height=150
# ).repeat(
#     repeat=columns,
#     columns=15,
# ).configure_axisY(
#     titleAngle=0,
# )
chart = (
    alt.Chart(df)
    .mark_rect()
    .encode(
        alt.X(alt.repeat("column"), type="nominal").axis(labels=False, labelLimit=0),
        alt.Y(alt.repeat("row"), type="nominal").axis(labels=False, labelLimit=0),
        # alt.Y("newsint:N", axis=alt.Axis(labels=False)),
        color=alt.Color("count():Q", legend=None),
    )
    .properties(width=150, height=150)
    .repeat(
        column=columns,
        row=columns,
    )
    .configure_axisY(
        titleAngle=0,
    )
)

chart.save("3_pair_plots.png")
import ipdb

ipdb.set_trace()
