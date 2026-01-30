## REST API
import flask, numpy, pandas as pd
from scipy.interpolate import PchipInterpolator
app = flask.Flask("Yield Curve Application")

all_df = pd.read_csv("all_df.csv", parse_dates=["Date"])

#Building the yield curve
def build_curve(country, date):
    date = pd.to_datetime(date)

    day = all_df[(all_df["Country"]==country) & (all_df["Date"]==date)][["Maturity","Yield"]].copy()

    if day.empty:
        raise ValueError(f"No data for the {country} on {date.date().strftime("%d %b %Y")}")

    #Though the data is good already, for consistency we will sort and clean appropriately.
    day = day.sort_values("Maturity").drop_duplicates(subset=["Maturity"])

    #Converting the (maturity,yield) data -> NumPy arrays
    x = day["Maturity"].to_numpy()
    y = day["Yield"].to_numpy()

    #Using piecewise cubic Hermite interpolation and flat extrapolation 
    if len(x) >= 3:
        interp = PchipInterpolator(x,y, extrapolate = False)
        def f(maturity):
            if maturity <= x[0]: return y[0]
            if maturity >= x[-1]: return y[-1]
            return interp(maturity)
        return f

    #Else, if you can't PCHIP, we just linearly interpolate instead and call it a day 
    def f(maturity):
        if maturity <= x[0]: return y[0]
        if maturity >= x[-1]: return y[-1]
        return np.interp(maturity, x, y)
    return f


## /latest
#Find the latest available date in all_df
def get_latest_date(country):
    dates = all_df[all_df["Country"]==country]["Date"]
    dates = dates.sort_values(ascending=False)
    dates = dates.reset_index(drop=True)
    return dates[0]
    
@app.route("/latest")
def latest():
    #The only arguments for /latest should be Country and Maturity
    args = flask.request.args
    
    #Data validation on parameters
    try:
        maturity = float(args.get("maturity"))
    except:
        return "Error: maturity should be float.", 400

    country = args.get("country").upper()
    if country not in ["US","UK"]:
        return "Error: country should be US or UK.", 400

    #Returning JSON
    date = pd.to_datetime(get_latest_date(country))

    return ({
            "date":date.strftime("%x"),
            "country": country,
            "maturity": maturity,
            "yield": float(build_curve(country, date)(maturity))/100
        })

## /timeseries
@app.route("/timeseries")
def timeseries():
    #Arguments for /timeseries should be Country, Maturity, Startdate, Enddate
    args = flask.request.args

    ####Data validation on parameters
    try: 
        maturity = float(args.get("maturity"))
    except: 
        return "Error: maturity should be float.", 400

    start = pd.to_datetime(args.get("start"), errors="coerce")
    end = pd.to_datetime(args.get("end"), errors="coerce")
    if pd.isna(start):
        start = pd.to_datetime("2024-01-01")
    if pd.isna(end):
        end = pd.to_datetime("now")
    
    country = args.get("country").upper()
    if country not in ["US","UK"]:
        return "Error: country should be US or UK.", 400

    dates = all_df[(start <= all_df["Date"]) & (all_df["Date"] <= end) & (all_df["Country"] == country)]["Date"]
    dates = dates.unique()

    data = []
    for date in dates:
        data.append({"date":date.strftime("%x"), "yield":float(build_curve(country,date)(maturity))/100})

    return ({
            "country": country,
            "maturity": maturity,
            "data": data
        })

app.run()
