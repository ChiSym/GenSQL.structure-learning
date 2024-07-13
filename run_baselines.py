import pandas as pd

from sdv.metadata import SingleTableMetadata
from sdv.single_table import GaussianCopulaSynthesizer
from sdv.single_table import CTGANSynthesizer

df = pd.read_csv("data/ignored.csv")

metadata = SingleTableMetadata()
metadata.detect_from_dataframe(data=df)

gan = CTGANSynthesizer(metadata)
gan.fit(df)
gan_df = gan.sample(len(df))
gan_df.to_csv("data/synthetic-data-gan.csv", index=False)

copula = GaussianCopulaSynthesizer(metadata)
copula.fit(df)
cop_df = copula.sample(len(df))
cop_df.to_csv("data/synthetic-data-copula.csv", index=False)
