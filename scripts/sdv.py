
from sdv.single_table import GaussianCopulaSynthesizer
from sdv.single_table import CTGANSynthesizer

from sdv.metadata import SingleTableMetadata

import pandas as pd

metadata = SingleTableMetadata()

df = pd.read_csv("data/ignored.csv")
metadata.detect_from_dataframe(data=df)
metadata.primary_key = None

print("Fitting GAN...")
gan = CTGANSynthesizer(metadata)
gan.fit(df)
gan_df = gan.sample(len(df))
gan_df.to_csv("data/synthetic-data-gan.csv", index=False)
print("...done")
print("")


print("Fitting Copula...")
copula = GaussianCopulaSynthesizer(metadata)
copula.fit(df)
cop_df = copula.sample(df.shape[0])
cop_df.to_csv("data/synthetic-data-copula.csv", index=False)
print("...done")
print("")












