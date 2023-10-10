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

n_models = len(spe.children)

i = 0
years = [2008, 2012, 2016, 2020]
year_list = []
ps = np.zeros(len(years) * n_models)
for year in years:
    for child_spe in spe.children:
        cspe = child_spe.constrain({Id("year"): str(year)})
        logp = cspe.logprob(Id("vv_turnout_gvm") << {"Voted"})
        year_list.append(year)
        ps[i] = np.exp(logp)
        i += 1

simple_results_df = pd.DataFrame({"year": year_list, "probability_turnout": ps})


simple_line = (
    alt.Chart(simple_results_df, title="Respondent turnout probability by year")
    .mark_line()
    .encode(
        x=alt.X("year:Q").axis(values=[2008, 2012, 2016, 2020], format="d"),
        y=alt.Y("mean(probability_turnout):Q", title="turnout probability").scale(
            zero=False
        ),
    )
)
simple_band = (
    alt.Chart(simple_results_df)
    .mark_errorband(extent="ci")
    .encode(
        x=alt.X("year:Q").axis(values=[2008, 2012, 2016, 2020], format="d"),
        y=alt.Y("probability_turnout:Q").scale(zero=False),
    )
)

simple_chart = simple_line + simple_band

simple_chart.save("simple_turnout_year_newsint.png")


with open("data/mapping-table.edn", "rb") as f:
    mapping_table = edn_format.loads(f.read())

vars = [c for c in mapping_table.keys() if c not in ["year", "vv_turnout_gvm", "age"]]

memo = Memo()


def possible_values(X):
    return mapping_table[X].keys()


def mutual_information(spe, X, Y, memo):
    possible_X_values = possible_values(X)
    possible_Y_values = possible_values(Y)

    mi = 0

    for x, y in product(possible_X_values, possible_Y_values):
        log_px = spe.logprob(Id(X) << {x}, memo)
        log_py = spe.logprob(Id(Y) << {y}, memo)
        log_pxy = spe.logprob((Id(X) << {x}) & (Id(Y) << {y}), memo)
        mi += np.exp(log_pxy) * (log_pxy - log_px - log_py)

    return mi


def conditional_mutual_information(spe, X, Y, Z, memo):
    possible_Z_values = possible_values(Z)

    mi = 0

    for z in possible_Z_values:
        log_pz = spe.logprob(Id(Z) << {z}, memo)

        cspe = spe.constrain({Id(Z): z}, memo)

        mi += np.exp(log_pz) * mutual_information(cspe, X, Y, memo)

    return mi


# cmis = [
#     conditional_mutual_information(
#         spe, "year", "vv_turnout_gvm", condition_var, memo)
#     for condition_var in tqdm(vars)]

year_list = []
newsint_list = []
p_turnout = []

for child_spe in tqdm(spe.children):
    for year in years:
        year_spe = child_spe.constrain({Id("year"): str(year)})
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

line = (
    alt.Chart(results_df)
    .mark_line()
    .encode(
        x=alt.X("year:Q").axis(values=[2008, 2012, 2016, 2020], format="d"),
        y=alt.Y("mean(p_turnout):Q", title="turnout probability").scale(zero=False),
    )
    .properties(
        width=150,
    )
)

band = (
    alt.Chart(results_df)
    .mark_errorband(extent="ci")
    .encode(
        x=alt.X("year:Q").axis(values=[2008, 2012, 2016, 2020], format="d"),
        y=alt.Y("p_turnout:Q").scale(zero=False),
    )
    .properties(
        width=150,
    )
)

chart = (line + band).facet(
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

chart.save("turnout_year_newsint.png")
