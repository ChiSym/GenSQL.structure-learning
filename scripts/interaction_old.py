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

with open("data/sppl/merged.json", "rb") as f:
    metadata = json.load(f)
    spe = spe_from_dict(metadata)

with open("data/mapping-table.edn", "rb") as f:
    mapping_table = edn_format.loads(f.read())

year_list = []
newsint_list = []
p_turnout = []

for year in tqdm(years):
    year_spe = spe.constrain({Id("year"): str(year)})
    for newsint in possible_values("newsint"):
        cspe = year_spe.constrain({Id("newsint"): newsint})
        log_p = cspe.logprob(Id("vv_turnout_gvm") << {"Voted"})
        p = np.exp(log_p)
        p_turnout.append(p)
        year_list.append(year)
        newsint_list.append(newsint)

results_df = pd.DataFrame(
    {"year": year_list, "newsint": newsint_list, "p_turnout": p_turnout}
)

chart = (
    alt.Chart(results_df)
    .mark_line()
    .encode(
        x=alt.X("year:Q").axis(values=[2008, 2012, 2016, 2020], format="d"),
        y=alt.Y("p_turnout:Q", title="turnout probability").scale(zero=False),
    )
    .properties(
        width=150,
    )
    .facet(
        column=alt.Column(
            "newsint:N",
            sort=[
                "Don't Know",
                "Hardly at all",
                "Only now and then",
                "Some of the time",
                "Most of the time",
            ],
            title=[
                "Respondent turnout probability by year",
                "split by how often they follow political news",
            ],
        )
    )
)

chart.save("turnout_year_newsint.png")
