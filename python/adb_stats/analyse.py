import pandas as pd
import requests_cache
from argparse import ArgumentParser
from bs4 import BeautifulSoup
from sklearn.preprocessing import minmax_scale

session = requests_cache.CachedSession(
    'web_cache',
    backend='sqlite',
    expire_after=365 * 86400
)


def convert_duration(duration_str):
    try:
        h, m, s = map(int, duration_str.split(":"))
        return h * 3600 + m * 60 + s
    except ValueError:
        m, s = map(int, duration_str.split(":"))
        return m * 60 + s


def scrape_app_name(package_name):
    play_url = "https://play.google.com/store/apps/details?id=" + package_name
    response = session.get(play_url)
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.find("h1").find("span").text


def main():
    parser = ArgumentParser(description="analyze Android app usage statistics")

    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="usagestats_yearly_packages.csv",
        help="path to the input CSV file containing app usage statistics"
    )
    parser.add_argument(
        "top_n",
        type=int,
        default=50,
        help="number of top apps to display"
    )

    args = parser.parse_args()

    df: pd.DataFrame = pd.read_csv(
        args.input,
        dtype={
            "package":          "string",
            "appLaunchCount":   "int64",
            "errorCount":       "int64"
        },
        parse_dates=[
            "lastTimeUsed",
            "lastTimeVisible",
            "lastTimeComponentUsed",
            "lastTimeFS"
        ]
    )

    duration_cols = [
        "totalTimeUsed",
        "totalTimeVisible",
        "totalTimeFS"
    ]

    for col in duration_cols:
        df[col + "Seconds"] = df[col].apply(convert_duration)
        df = df.drop(columns=[col])

    df["weightedScore"] = (
        minmax_scale(df["appLaunchCount"]) * 0.5 +
        minmax_scale(df["totalTimeUsedSeconds"]) * 0.5
    )

    top_df = df.sort_values(by=["weightedScore"], ascending=False).head(n=args.top_n)
    top_df["app"] = top_df["package"].apply(scrape_app_name)

    top_df[["package", "app"]].to_csv(
        f"top_{args.top_n}_apps.csv",
        index=False
    )


if __name__ == "__main__":
    main()
