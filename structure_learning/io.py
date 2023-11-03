import polars as pl

def read_csv(data_filename, column_models):    
    return pl.read_csv(
        data_filename, 
        dtypes={
            cm.name: pl.Utf8 if cm.distribution == "categorical" else pl.Float64
            for cm in column_models
        }
    )