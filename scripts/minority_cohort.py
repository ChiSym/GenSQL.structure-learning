import pandas as pd

df = pd.read_csv("data/preprocessed.csv")

# Conditions
conds = ["gender", "educ", "race_ethnicity"]
N = 1000
p_asians = 0.8
df = df[df["religion_importance"] == "Very Important"]
dfa = df[df["race_ethnicity"] == "Asian"]
dfna = df[df["race_ethnicity"] != "Asian"]

df_out= pd.concat([
        dfa.sample(int(N*p_asians), random_state=42),
        dfna.sample(int(N*(1-p_asians)), random_state=42),
        ])

df_out = df_out.sample(frac=1, random_state=42)
print(df_out["race_ethnicity"].value_counts())
df_out[conds].to_csv("data/minority-cohort.csv", index=False)
# targets:
# Ideology, "race_ethnicity"
