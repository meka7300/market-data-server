import pandas as pd, numpy as np
import requests
from io import StringIO

us_series = ["DGS1MO", "DGS3MO", "DGS6MO", "DGS1", "DGS2", "DGS5", "DGS10", "DGS30"]
us_df = None
us_url = "https://fred.stlouisfed.org/graph/fredgraph.csv"

#Pull CSV from FRED website using IDs above
#Loop through all IDs and join all dataframes into one.
for series in us_series:
    params = {
        "id" : series,
        "cosd" : "2024-01-01",
    }
    r = requests.get(us_url, params=params, timeout=30)
    tmp = pd.read_csv(StringIO(r.text))
    tmp["observation_date"] = pd.to_datetime(tmp["observation_date"])
    tmp = tmp.set_index("observation_date")

    if us_df is None:
        us_df = tmp
    else:
        us_df = us_df.join(tmp,how="outer")

#Melting dataframes + adding necessary columns
us_df = us_df.reset_index().melt(
    id_vars = ["observation_date"],
    var_name = "Maturity",
    value_name = "Yield"
)
us_df["Country"] = "US"
us_df["Instrument"] = "Treasury"

#Renaming FRED IDs to maturity lengths in years
us_df = us_df.rename(columns={"observation_date":"Date"})
us_df.Maturity = us_df.Maturity.map({"DGS1MO":1/12, 
                    "DGS3MO":3/12,
                    "DGS6MO":6/12,
                    "DGS1":1,
                    "DGS2":2,
                    "DGS5":5,
                    "DGS10":10,
                    "DGS30":30})

## UK data
url = "https://www.bankofengland.co.uk/boeapps/iadb/fromshowcolumns.asp"

params = {
    "csv.x": "yes",
    "Datefrom": "01/Jan/2024",
    "Dateto": "now",
    "SeriesCodes": "IUDSNPY,IUDMNPY,IUDLNPY",
    "CSVF": "TN",
    "UsingCodes": "Y",
}
headers = {
    "User-Agent": "Mozilla/5.0"
}
r2 = requests.get(url, params=params, headers = headers, timeout=30)
uk_df = pd.read_csv(StringIO(r2.text))

uk_df = uk_df.melt(
    id_vars = ["DATE"],
    var_name = "Maturity",
    value_name = "Yield"
)

uk_df["Country"] = "UK"
uk_df["Instrument"] = "Gilt"

uk_df = uk_df.rename(columns={"DATE":"Date"})
uk_df.Maturity = uk_df.Maturity.map({"IUDSNPY":5., 
                    "IUDMNPY":10,
                    "IUDLNPY":20,
})
uk_df["Date"] = pd.to_datetime(uk_df["Date"])

all_df = pd.concat([us_df, uk_df], ignore_index=True)
all_df = all_df.dropna(subset=["Yield"]).reset_index(drop=True)
all_df.to_csv("all_df.csv")

