import urllib.request
import pandas as pd
import time
from tqdm import tqdm


def main():
    print("Retrieving player URLs...")
    master_df = getPlayerURLs("https://www.basketball-reference.com/leagues/NBA_2019_per_game.html")

    print("Getting long-term player data...")
    refreshData(master_df)

    print("Writing to CSV...")
    master_df.to_csv("Long-Term Stats.csv")


def refreshData(master_df):
    rows = []
    for index, row in tqdm(master_df.iterrows()):
        player_data = pull_data(getSourceCode("https://www.basketball-reference.com" + row["player_url"]))
        rows.append(player_data)

    for i in range(0, len(rows)):
        for stat in rows[i].keys():
            master_df.at[i, stat] = rows[i][stat]


def pull_data(source_code):
    row_data = {}
    row_data["height"] = convert_height(findBetween(source_code, "itemprop=\"height\">", "<"))
    row_data["weight"] = findBetween(source_code, "itemprop=\"weight\">", "<")
    row_data["experience"] = findBetween(source_code, "<tbody>", "</tbody>").count("class=\"full_table\"")
    row_data["all_nba"] = findBetween(source_code, "leaderboard_all_league", "</div>").count("All-NBA")

    source_table = findBetween(source_code, "<tbody>", "</tbody>")
    source_rows = source_table.split("class=\"full_table\"")[1:]
    for source_row in source_rows:
        year = findBetween(source_row, "/leagues/NBA_", ".html")
        if year != "2019":
            row_data.update(split_stat_row(source_row[:source_row.find("</tr>")], year))

    return row_data


def split_stat_row(row, year):
    row_data = {}
    columns = row.split("data-stat")[3:]
    for column in columns:
        stat = findBetween(column, "=\"", "\"") + "_" + year
        value = findBetween(column, ">", "</td>")
        if "strong" in value:
            value = findBetween(value, ">", "<")

        if stat != "team_id" + "_" + year and stat != "lg_id" + "_" + year:
            row_data[stat] = value
    return row_data


def convert_height(original):
    feet = int(original.split("-")[0])
    inches = int(original.split("-")[1])
    return round(feet + (inches / 12), 4)


def getPlayerURLs(main_url):
    source = getSourceCode(main_url)
    source_table = findBetween(source, "<tbody>", "</tbody>")
    source_rows = source_table.split("<tr class=\"full_table\" >")[1:]
    rows = []
    for source_row in source_rows:
        row_data = {}
        row_data["player_id"] = findBetween(source_row, "data-append-csv=\"", "\"")
        row_data["player_url"] = findBetween(source_row, "href=\"", "\"")
        rows.append(row_data)
    return pd.DataFrame(rows)


def getSourceCode(inputURL):
    webURL = urllib.request.urlopen(inputURL)
    data = webURL.read()
    return data.decode(webURL.headers.get_content_charset(), errors="replace")


def findBetween(string, substring_1, substring_2, after_index=0):
    start = string.find(substring_1, after_index) + len(substring_1)
    end = string.find(substring_2, start)
    return string[start: end]


if __name__ == "__main__":
    print("Starting up...")
    start = time.time()
    main()
    print("Run time:", round(time.time() - start, 3))
