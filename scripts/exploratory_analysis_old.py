import pandas as pd
import altair as alt
import numpy as np

real_data_path = "data/data.csv"
lpm_data_path = "data/synthetic-data-iql.csv"
ctgan_data_path = "data/synthetic-data-ctgan.csv"
copula_data_path = "data/synthetic-data-copula.csv"

data_paths = [real_data_path, lpm_data_path, ctgan_data_path, copula_data_path]

dfs = [pd.read_csv(data_path) for data_path in data_paths]


sources = ["Real", "LPM", "CTGAN", "Copula"]

cols_to_filter = ["Day", "Prostate_Specific_Antigen"]
# cols_to_filter = ["Creatinine", "Sodium"]
# cols_to_filter = ["Sodium", "Blood_Urea_Nitrogen"]
# cols_to_filter = [c for c in dfs[0].select_dtypes([np.number]).columns]

col_range_dims = {
    col: [dfs[0][col].quantile(0.01), dfs[0][col].quantile(0.99)]
    for col in cols_to_filter
}


def winsorize(df, cols_to_filter):
    for col in cols_to_filter:
        q_low, q_hi = col_range_dims[col]
        df = df[(df[col] <= q_hi) & (df[col] >= q_low)]

    return df


def add_source(df, source):
    df["source"] = source

    return df


dfs = [winsorize(df, cols_to_filter) for df in dfs]
dfs = [add_source(df, source) for df, source in zip(dfs, sources)]

full_df = pd.concat(dfs)

# lpm_df = full_df[full_df["source"].isin(["Real", "LPM"])]
# ctgan_df = full_df[full_df["source"].isin(["Real", "CTGAN"])]
# copula_df = full_df[full_df["source"].isin(["Real", "Copula"])]
# real_df = full_df[full_df["source"].isin(["Real"])]

# models = ["Real", "LPM", "CTGAN", "Copula"]

# filtered_dfs = [full_df[full_df["source"].isin([model])] for model in models]

chart = (
    alt.Chart(full_df)
    .mark_rect()
    .encode(
        # x='Blood_Urea_Nitrogen:Q',
        x=alt.X(f"{cols_to_filter[0]}:Q").scale(zero=False).bin(maxbins=30),
        y=alt.Y(f"{cols_to_filter[1]}:Q").scale(zero=False).bin(maxbins=30),
        color=alt.Color("count():Q", legend=None).scale(scheme="greenblue")
        # color=alt.Color("source:N", sort=["Real", model])
    )
).facet(
    facet=alt.Facet("source:N", title=None),
)
chart.save(f"full_pairplot_{cols_to_filter[0]}_{cols_to_filter[1]}.png")
# lpm_df = lpm_df[cols_to_filter]

# chart = alt.Chart(lpm_df).mark_circle().encode(
#     alt.X(alt.repeat("column"), type='quantitative').scale(zero=False),
#     alt.Y(alt.repeat("row"), type='quantitative').scale(zero=False),
#     color='source:N'
# ).properties(
#     width=150,
#     height=150
# ).repeat(
#     row=cols_to_filter,
#     column=cols_to_filter,
# )

# chart.save(f"lpm_pairplot_all.png")

# chart = (
#     alt.Chart(real_df)
#     .mark_point(opacity=.5)
#     .encode(
#         # x='Blood_Urea_Nitrogen:Q',
#         x=alt.X(f"{cols_to_filter[0]}:Q"),
#         y=alt.Y(f"{cols_to_filter[1]}:Q"),
#         # color=alt.Color("source:N", sort=["Real", "LPM"])
#     )
# )


# import ipdb; ipdb.set_trace(0)
# chart.save(f"real_pairplot_{cols_to_filter[0]}_{cols_to_filter[1]}.png")
# real_df = real_df[cols_to_filter]
# chart = alt.Chart(real_df).mark_circle().encode(
#     alt.X(alt.repeat("column"), type='quantitative').scale(zero=False),
#     alt.Y(alt.repeat("row"), type='quantitative').scale(zero=False),
#     color='source:N'
# ).properties(
#     width=150,
#     height=150
# ).repeat(
#     row=cols_to_filter,
#     column=cols_to_filter,
# )


# chart.save(f"real_pairplot_all.png")
