import os
import re
import pandas as pd
import requests_cache
from argparse import ArgumentParser
from bs4 import BeautifulSoup
from pathlib import Path
from sklearn.preprocessing import minmax_scale

session = requests_cache.CachedSession(
    'web_cache',
    backend='sqlite',
    expire_after=365 * 86400
)


def parse_line_into_pairs(line):
    pattern = re.compile(r'(\w+)=(?:"((?:[^"\\]|\\.)*)"|([^\s]+))', re.VERBOSE)

    result = {}
    for match in pattern.finditer(line):
        key = match.group(1)
        value = (
            match.group(2)
            if match.group(2) is not None
            else match.group(3)
        )
        if value is not None:
            value = value.replace(r'\"', '"')
        result[key] = value
    return result


def convert_to_records(text):
    records = []
    for line in text.splitlines():
        line = line.strip()
        records.append(parse_line_into_pairs(line))
    return records


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
    parser = ArgumentParser(description="analyze android app usage statistics")
    parser.add_argument(
        "input_file",
        type=str,
        help="path to the input CSV file containing app usage statistics"
    )
    parser.add_argument(
        "-t",
        "--top-n",
        type=int,
        default=50,
        help="number of top apps to display"
    )
    args = parser.parse_args()

    input_file = Path(args.input_file).absolute()
    os.chdir(input_file.absolute().parent)

    out_file = f"{input_file.stem}.csv"
    with open(input_file, "r") as f:
        dataframe = pd.DataFrame(convert_to_records(f.read()))
        dataframe.to_csv(out_file, index=False)

    df: pd.DataFrame = pd.read_csv(
        out_file,
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

    top_df = df.sort_values(
        by=["weightedScore"],
        ascending=False
    ).head(n=args.top_n)
    top_df["app"] = top_df["package"].apply(scrape_app_name)

    top_df[["package", "app"]].to_csv(
        f"top_{args.top_n}_apps.csv",
        index=False
    )


if __name__ == "__main__":
    main()
