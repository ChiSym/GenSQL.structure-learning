import pandas as pd
import altair as alt

data_path = "data/data.csv"
json_data_path = "data/subsampled.json"

df = pd.read_csv(data_path)

cols_to_filter = [
    "Prostate_Specific_Antigen",
    "Lymphocytes"
]

for col in cols_to_filter:
    q_low = df[col].quantile(0.01)
    q_hi  = df[col].quantile(0.99)

    df = df[(df[col] < q_hi) & (df[col] > q_low)]

chart = alt.Chart(df).mark_circle().encode(
    # x='Blood_Urea_Nitrogen:Q',
    x='Prostate_Specific_Antigen:Q',
    y='Lymphocytes:Q',
    # color="Blood_Urea_Nitrogen:Q"
)

chart.save("pairplot.png")

import ipdb; ipdb.set_trace()

