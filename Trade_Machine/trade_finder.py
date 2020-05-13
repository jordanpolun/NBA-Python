import math
import time
import urllib.request
from itertools import combinations
import pandas as pd
import numpy as np

class Trade:
    trade_id = 0
    team_a = ""
    team_b = ""
    a_assets = pd.DataFrame()
    b_assets = pd.DataFrame()
    all_assets = pd.DataFrame()
    score = 0

    def __init__(self, team_a, a_assets, team_b, b_assets, trade_id):
        self.team_a = team_a
        self.a_assets = a_assets
        self.team_b = team_b
        self.b_assets = b_assets
        self.trade_id = trade_id
        self.score = self.scoreTrade()

    def scoreTrade(self):
        score_a = self.scoreTradeForTeam(self.team_a, self.team_b, self.a_assets, self.b_assets)
        score_b = self.scoreTradeForTeam(self.team_b, self.team_a, self.b_assets, self.a_assets)
        return min(score_a, score_b)

    def scoreTradeForTeam(self, team, trade_team, team_assets, trade_team_assets):
        if team["goal"] == "contending":
            # Test if worp, current_value, and expected wins are improved.
            value = 0
            stats = ["vorp", "current_value", "ws", "per", "bpm"]
            for stat in stats:
                if sum(trade_team_assets[stat]) > sum(team_assets[stat]):
                    value += 1
                if np.mean(trade_team_assets[stat]) > np.mean(team_assets[stat]):
                    value += 1

            return (value/(len(stats) * 2)) * 10

        if team["goal"] == "buying":
            return 0

        if team["goal"] == "rebuilding":
            return 0

        if team["goal"] == "selling":
            return 0


def main():
    print("Refreshing latest player data...")
    start = time.time()
    # refreshPlayerData()
    print(round(time.time() - start, 3), "\n")

    print("Refreshing latest team data...")
    start = time.time()
    # refreshTeamData()
    print(round(time.time() - start, 3), "\n")

    print("Reading all data...")
    start = time.time()
    player_df, team_df = readAllStatsData()
    print(round(time.time() - start, 3), "\n")

    print("Finding targets for teams...")
    # This returns a dictionary of { team_id : DF of all the players and picks they want }
    start = time.time()
    targets = findAllTargets(player_df, team_df)
    print(round(time.time() - start, 3), "\n")

    print("Removing non-targets from DataFrame...")
    start = time.time()
    player_df = removeNonTargets(player_df, targets)
    print(round(time.time() - start, 3), "\n")

    print("Finding intersections...")
    # This returns a list of ( team_a_id, team_b_id, DF of players_involved )
    start = time.time()
    intersections = findIntersections(targets, team_df)[:5]
    print(round(time.time() - start, 3), "\n")

    print("Generating every trade from intersections...")
    start = time.time()
    all_trades = generateAllTrades(intersections, team_df)
    print(round(time.time() - start, 3), "\n")


def generateAllTrades(intersections, team_df):
    trades = []
    trade_id = 0

    for team_a_id, team_b_id, players_involved in intersections:
        team_a_row = team_df[team_df["team_id"] == team_a_id].iloc[0]
        team_a_asset_ids = players_involved[players_involved["team"] == team_a_id]["player_id"]
        trade_packages_a = []

        team_b_row = team_df[team_df["team_id"] == team_b_id].iloc[0]
        team_b_asset_ids = players_involved[players_involved["team"] == team_b_id]["player_id"]
        trade_packages_b = []

        # Put together team_a trade packages
        for r in range(0, len(team_a_asset_ids)):
            for trade_package_ids in combinations(team_a_asset_ids, r):
                trade_package = players_involved[players_involved["player_id"].isin(trade_package_ids)]
                trade_packages_a.append(trade_package)

        # Put together team_b trade packages
        for r in range(0, len(team_b_asset_ids)):
            for trade_package_ids in combinations(team_b_asset_ids, r):
                trade_package = players_involved[players_involved["player_id"].isin(trade_package_ids)]
                trade_packages_b.append(trade_package)

        # Put every combination of the teams' trade packages together in trades
        for package_a in trade_packages_a:
            for package_b in trade_packages_b:
                trades.append(Trade(team_a_row, package_a, team_b_row, package_b, trade_id))
                trade_id += 1

    print("Found", len(trades), "total possible trades.")
    return trades


def findIntersections(targets, team_df):
    intersections = [] # tuple of ( team_a_id, team_b_id, DF of players_involved )

    for team_a_id, team_b_id in combinations(team_df["team_id"], 2):
        team_a_df = targets[team_a_id]
        team_b_df = targets[team_b_id]

        a_to_b = team_b_df[team_b_df["team"] == team_a_id]
        b_to_a = team_a_df[team_a_df["team"] == team_b_id]

        if len(a_to_b) > 0 and len(b_to_a) > 0:
            involved_players = pd.concat([a_to_b, b_to_a]).dropna(subset=["name"])
            intersections.append((team_a_id, team_b_id, involved_players))

    return intersections


def removeNonTargets(player_df, targets):
    for team in targets.keys():
        print(len(targets[team]))


def findAllTargets(player_df, team_df):
    targets_dict = {}
    for index, team in team_df.iterrows():
        targets_dict[team["team_id"]] = getTeamTargets(team, player_df, team_df)
    return targets_dict


def getTeamTargets(team, player_df, team_df):
    eligible_df = player_df[player_df["team"] != team["team_id"]]
    if team["goal"] == "contending":
        # A contending team would only bother trading for a good player in the top 20 of the stat they are bad in
        eligible_df = eligible_df[eligible_df["current_value"] > 6]
        wishlist = pd.DataFrame()
        if team["need_def"]:
            wishlist = wishlist.append(eligible_df.nsmallest(20, ["def_rtg"]), ignore_index=True)
        if team["need_off"]:
            wishlist = wishlist.append(eligible_df.nlargest(20, ["off_rtg"]), ignore_index=True)
        if team["need_3p"]:
            wishlist = wishlist.append(eligible_df.nlargest(20, ["fg3_pct"]), ignore_index=True)
        if team["need_trb"]:
            wishlist = wishlist.append(eligible_df.nlargest(20, ["trb_pct"]), ignore_index=True)
        if team["need_ts"]:
            wishlist = wishlist.append(eligible_df.nlargest(20, ["ts_pct"]), ignore_index=True)
        wishlist.drop_duplicates(inplace=True)
        return wishlist

    if team["goal"] == "buying":
        # A buying team would only want players that are currently good and will stay that good in the future
        eligible_df = eligible_df[eligible_df["current_value"] > 5]
        eligible_df = eligible_df[eligible_df["future_value"] > 5]
        wishlist = pd.DataFrame()
        if team["need_def"]:
            wishlist = wishlist.append(eligible_df.nsmallest(30, ["def_rtg"]), ignore_index=True)
        if team["need_off"]:
            wishlist = wishlist.append(eligible_df.nlargest(30, ["off_rtg"]), ignore_index=True)
        if team["need_3p"]:
            wishlist = wishlist.append(eligible_df.nlargest(30, ["fg3_pct"]), ignore_index=True)
        if team["need_trb"]:
            wishlist = wishlist.append(eligible_df.nlargest(30, ["trb_pct"]), ignore_index=True)
        if team["need_ts"]:
            wishlist = wishlist.append(eligible_df.nlargest(30, ["ts_pct"]), ignore_index=True)
        wishlist.drop_duplicates(inplace=True)
        return wishlist

    if team["goal"] == "rebuilding":
        # A rebuilding team is looking for young future stars and draft picks
        wishlist = eligible_df[(eligible_df["future_value"] > 7) & \
                                (eligible_df["age"] < 25)]
        partner_teams = team_df[team_df["name"] != team["name"]]
        for index, partner in partner_teams.iterrows():
            wishlist = wishlist.append(
                {"player_id": partner["team_id"],
                 "team": partner["team_id"],
                 "current_value": partner["pick_value_1"],
                 "future_value": partner["pick_value_1"]},
                ignore_index=True)
        return wishlist

    if team["goal"] == "selling":
        # A selling team would only want to take in expiring deals and draft picks
        wishlist = eligible_df[(eligible_df["expiring"]) & \
                               (eligible_df["y1"] > 5000000)]
        partner_teams = team_df[team_df["name"] != team["name"]]
        for index, partner in partner_teams.nlargest(14, ["pick_value_1"]).iterrows():
            wishlist = wishlist.append(
                {"player_id": partner["team_id"],
                 "team": partner["team_id"],
                 "current_value": partner["pick_value_1"],
                 "future_value": partner["pick_value_1"]},
                ignore_index=True)
        return wishlist


def readAllStatsData():
    player_df = pd.read_csv("Player Stats.csv").apply(pd.to_numeric, errors="ignore")
    team_df = pd.read_csv("Team Stats.csv").apply(pd.to_numeric, errors="ignore")
    return player_df, team_df


def refreshPlayerData():
    print("Pulling per game stats...")
    per_game_df = generateStatsDF("https://www.basketball-reference.com/leagues/NBA_2019_per_game.html")

    print("Pulling season totals...")
    totals_df = generateStatsDF("https://www.basketball-reference.com/leagues/NBA_2019_totals.html")

    print("Pulling per 36 minutes stats...")
    per_36_df = generateStatsDF("https://www.basketball-reference.com/leagues/NBA_2019_per_minute.html")

    print("Pulling per 100 possessions stats...")
    per_100_df = generateStatsDF("https://www.basketball-reference.com/leagues/NBA_2019_per_poss.html")

    print("Pulling advanced stats...")
    advanced_df = generateStatsDF("https://www.basketball-reference.com/leagues/NBA_2019_advanced.html")

    print("Combining DataFrames...")
    player_df = pd.concat([per_game_df, totals_df, per_36_df, per_100_df, advanced_df], axis=1, join="inner")
    player_df = player_df.loc[:, ~player_df.columns.duplicated()]

    print("Calculating player fantasy points...")
    addFPColumn(player_df)
    player_df = player_df.sort_values(by=["fp_per_g"], ascending=False)

    print("Adding in salaries...")
    addSalaries(player_df, "https://www.basketball-reference.com/contracts/players.html")
    player_df = player_df.apply(pd.to_numeric, errors="ignore")

    print("Assessing player contract quality...")
    addPlayerAttributes(player_df)

    print("Removing free agents...")
    player_df.dropna(subset=["team"], inplace=True)

    print("Saving player data to CSV...")
    player_df.to_csv("Player Stats.csv")


def addPlayerAttributes(player_df):
    """
    This pulls in data from another CSV I have which has data that rarely changes (age, height, etc.)
    It then makes everything it can in the dataframe a numeric and replaces any blank spaces with -1
    It uses information in the long-term stats and player_df to find expiring contracts and bad contracts
    """

    expiring = []
    bad_salaries = []
    current_values = []
    future_values = []
    long_term_df = pd.read_csv("Long-Term Stats.csv").apply(pd.to_numeric, errors="ignore").fillna(-1)

    for index, row in player_df.iterrows():
        if row["y2"] == 0:
            expiring.append(True)
        else:
            expiring.append(False)

        bad_contract = isBadContract(index, row, long_term_df)
        bad_salaries.append(bad_contract)

        current_value, future_value = calculateTradeValue(row)
        current_values.append(current_value)
        future_values.append(future_value)
    current_values = convertTradeValues(current_values)
    future_values = convertTradeValues(future_values)

    player_df["worp"] = [2.7*x for x in player_df["vorp"]]
    player_df["expiring"] = expiring
    player_df["bad_contract"] = bad_salaries
    player_df["current_value"] = current_values
    player_df["future_value"] = future_values


def convertTradeValues(trade_values):
    """
    Convert traditional trade value scheme to a scale of 1-10
    """
    new_trade_values = []
    old_min = min(trade_values)
    old_max = max(trade_values)
    for tv in trade_values:
        new_tv = round((((tv - old_min) * (10 - 1)) / (old_max - old_min)) + 1, 3)
        new_trade_values.append(new_tv)
    return new_trade_values


def calculateTradeValue(row):
    """
    This will calculate trade value based on the formula on this website: https://www.nbastuffer.com/analytics101/trade-value/
    and this website: https://www.nbastuffer.com/analytics101/approximate-value/
    Credits=(Points)+(Rebounds)+(Assists)+(Steal)+(Blocks)-(Field Goals Missed)-(Free Throws Missed)-(Turnovers)
    Approximate Value = (Credits**(3/4) )/21
    Trade Value Formula=[(Approximate Value- 27-0.75*Age )^2( 27-0.75*Age +1)*Approximate Value]/190+(Approximate Value)*2/13
    """
    credits = row["pts"] + row["trb"] + row["ast"] + row["stl"] + row["blk"] - (row["fga"] - row["fg"]) - (
            row["fta"] - row["ft"]) - row["tov"]
    approximate_value = (credits ** (3 / 4)) / 21
    trade_value = ((approximate_value - 27 - 0.75 * row["age"]) ** 2 * (
            27 - 0.75 * row["age"] + 1) * approximate_value) / (190 + (approximate_value) * 2 / 13)

    if type(approximate_value) != float:
        approximate_value = approximate_value.real

    if type(trade_value) != float:
        trade_value = trade_value.real

    return approximate_value, trade_value


def isBadContract(index, row, long_term_df):
    """
    This calculates what a player's salary should be based on their stats
    It uses a formula from this webpage: https://prosportsanalytics.com/2017/06/01/predicting-nba-salaries-part-2/
    It then figures out whether it is a bad contract. A bad contract can either be at least one year where they are
    making more than 150% what they are supposed to, or at least two seasons where they make 125% each year
    """
    long_term_row = long_term_df.loc[long_term_df['player_id'] == index].iloc[0]

    y1_contract = math.exp(13.15 + (0.19 * long_term_row["experience"]) + (-0.01 * (long_term_row["experience"] ** 2)) + \
                           (0.05 * row["mp_per_g"]) + (0.02 * row["pts_per_mp"]) + (0.05 * long_term_row["all_nba"]) + \
                           (0.05 * row["ows"]) + (0.19 * row["dws"]) + 0.15)

    y2_pts = projectPTS(row, long_term_row)

    y2_contract = math.exp(
        13.15 + (0.19 * (1 + long_term_row["experience"])) + (-0.01 * (1 + (long_term_row["experience"] ** 2))) + \
        (0.05 * row["mp_per_g"]) + (0.02 * row["pts_per_mp"]) + (0.05 * long_term_row["all_nba"]) + \
        (0.05 * row["ows"]) + (0.19 * row["dws"]) + 0.15)

    if row["y1"] > y1_contract * 1.5 or (row["y1"] > y1_contract * 1.25 and row["y2"] > y2_contract * 1.25):
        return True

    return False


def projectPTS(row, long_term_row):
    """
    This will predict how many points a player will score next season,
    very loosely based off of the Simple Projection System. It takes a weighted
    sum of the points scored in previous seasons and then adjusts for age
    """
    pts_2019 = row["pts_per_g"] * 0.6
    pts_2018 = long_term_row["pts_per_g_2018"] * 0.3
    if pts_2018 == -1:
        pts_2018 = pts_2019
    pts_2017 = long_term_row["pts_per_g_2017"] * 0.1
    if pts_2017 == -1:
        pts_2017 = pts_2018
    unadjusted_pts_per_g = pts_2019 + pts_2018 + pts_2017

    if row["age"] < 28:
        return unadjusted_pts_per_g * (1 + ((row["age"] - 29) * 0.004))
    elif row["age"] > 28:
        return unadjusted_pts_per_g * (1 + ((row["age"] - 29) * 0.002))
    else:
        return unadjusted_pts_per_g


def addSalaries(player_df, url):
    """
    This will find the salary of every player getting paid by the NBA (even if not on a team).
    It does this for 6 years, so some (most) players will not have data for every column
    """
    source = getSourceCode(url)
    source_table = findBetween(source, "<tbody>", "</tbody>")
    source_rows = source_table.split("<tr ><th scope=\"row\"")[1:]
    for source_row in source_rows:
        player_id = findBetween(source_row, "data-append-csv=\"", "\"")
        if any(player_df.index == player_id):
            df_row_index = player_df.index[player_df.index == player_id][0]
            row_data = splitSalaryRow(source_row)
            for year in row_data.keys():
                player_df.at[df_row_index, year] = row_data[year]


def splitSalaryRow(row):
    """
    This breaks up a row of HTML into a dictionary of stats and their values for that row.
    In this case, it breaks up the row that contains a player's future earnings.
    """
    row_data = {}
    cells = row.split("data-stat=\"")[1:]
    for cell in cells:
        data_stat = cell[:2]
        if data_stat in ("y1", "y2", "y3", "y4", "y5", "y6"):
            money = findBetween(cell, "csk=\"", "\"")
            if "=" not in money:
                row_data[data_stat] = money
            else:
                row_data[data_stat] = 0
    row_data["team"] = findBetween(findBetween(row, "team_id\" >", "/a>"), ">", "<")
    return row_data


def addFPColumn(player_df):
    """
    This determines the average fantasy points gained per player based on the scale that is set for my fantasy league
    PTS = 1
    ORB = 1.5
    DRB = 1
    AST = 2
    STL = 2
    BLK = 3
    TOV = -1
    PF = -1
    Double double = 5
    """
    fp_per_g = []

    for index, row in player_df.iterrows():
        fantasy_points = row["pts_per_g"] + (row["orb_per_g"] * 1.5) + \
                         row["drb_per_g"] + (row["ast_per_g"] * 2.0) + \
                         (row["stl_per_g"] * 2.0) + (row["blk_per_g"] * 3.0)
        fantasy_points = fantasy_points - row["tov_per_g"] - row["pf_per_g"]

        dd_stats = (row["pts_per_g"], row["trb_per_g"], row["ast_per_g"], row["stl_per_g"], row["blk_per_g"])

        if sum(1 for e in dd_stats if e > 10.0) >= 2:
            fantasy_points = fantasy_points + 5

        fp_per_g.append(fantasy_points)

    for row in range(len(player_df)):
        fantasy_points = float(player_df.loc[row, "pts_per_g"]) + (float(player_df.loc[row, "orb_per_g"]) * 1.5) + \
                         float(player_df.loc[row, "drb_per_g"]) + (float(player_df.loc[row, "ast_per_g"]) * 2) + \
                         (float(player_df.loc[row, "stl_per_g"]) * 2) + (float(player_df.loc[row, "blk_per_g"]) * 3)
        fantasy_points = fantasy_points - float(player_df.loc[row, "tov_per_g"]) - float(player_df.loc[row, "pf_per_g"])

        dd_stats = (float(player_df.loc[row, "pts_per_g"]), float(player_df.loc[row, "trb_per_g"]),
                    float(player_df.loc[row, "ast_per_g"]), float(player_df.loc[row, "stl_per_g"]),
                    float(player_df.loc[row, "blk_per_g"]))
        if sum(1 for e in dd_stats if e > 10.0) >= 2:
            fantasy_points = fantasy_points + 5

        fp_per_g.append(fantasy_points)

    player_df["fp_per_g"] = fp_per_g


def refreshTeamData():
    """
    This separates HTML source code into tables which are fed into getTeamData, this will return a dataframe from
    the data in the table
    """
    source = getSourceCode("https://www.basketball-reference.com/leagues/NBA_2019.html")

    print("Pulling team per game stats...")
    per_game_df = getTeamData(source, "all_team-stats-per_game", suffix="_per_g")

    print("Pulling opponent per game stats...")
    opp_per_game_df = getTeamData(source, "all_opponent-stats-per_game", suffix="_per_g")

    print("Pulling team total stats...")
    totals_df = getTeamData(source, "all_team-stats-base")

    print("Pulling opponent total stats...")
    opp_totals_df = getTeamData(source, "all_opponent-stats-base")

    print("Pulling team per 100 possessions stats...")
    per_poss_df = getTeamData(source, "all_team-stats-per_poss", suffix="_per_poss")

    print("Pulling opponent per 100 possessions stats...")
    opp_per_poss_df = getTeamData(source, "all_opponent-stats-per_poss", suffix="_per_poss")

    print("Pulling miscellaneous team stats...")
    misc_df = getTeamData(source, "all_misc_stats")

    print("Concatenating team stats without duplicate columns...")
    team_df = pd.concat([per_game_df, opp_per_game_df, totals_df, opp_totals_df, per_poss_df, opp_per_poss_df, misc_df],
                        axis=1, join="inner")
    team_df = team_df.loc[:, ~team_df.columns.duplicated()]
    team_df = team_df.apply(pd.to_numeric, errors="ignore")

    print("Identifying team needs...")
    identifyTeamNeeds(team_df)

    print("Calculating draft pick value...")
    addPickValues(team_df)

    print("Saving team data to CSV")
    team_df.to_csv("Team Stats.csv")

    return team_df


def addPickValues(team_df):
    # for now, assuming every team has 1 first round and 1 second round pick
    rankings = team_df["losses"].rank()
    first_rounders = []
    second_rounders = []
    for i in rankings:
        pick_num = 31 - i
        first_rounders.append(getPickValue(pick_num))
        second_rounders.append(getPickValue(pick_num + 30))
    team_df["pick_value_1"] = first_rounders
    team_df["pick_value_2"] = second_rounders


def getPickValue(pick_number):
    # from https://www.82games.com/barzilai1.htm
    return round(0.974 * math.exp((-0.05531 * (pick_number - 1))), 3) * 10


def identifyTeamNeeds(team_df):
    """
    This will identify what a team is missing and what they're trying to move towards
        Find team goal (contending, buying, rebuilding, selling)
        Find team deficiencies (defense, rebounding, 3P%)
    """
    team_goals = []

    for index, row in team_df.iterrows():
        team_goals.append(identifyTeamGoal(row))

    team_df["goal"] = team_goals
    team_df["need_def"] = identifyDeficiencies(team_df, "def_rtg", smaller_better=True)
    team_df["need_off"] = identifyDeficiencies(team_df, "off_rtg", smaller_better=False)
    team_df["need_3p"] = identifyDeficiencies(team_df, "fg3_pct_per_g")
    team_df["need_trb"] = identifyDeficiencies(team_df, "trb_per_poss")
    team_df["need_ts"] = identifyDeficiencies(team_df, "ts_pct")


def identifyDeficiencies(team_df, stat, smaller_better=False):
    need_stat = []
    for index, row, in team_df.iterrows():
        if not smaller_better:
            if index in list(team_df.nlargest(10, stat).index.values.tolist()):
                need_stat.append(False)
            else:
                need_stat.append(True)
        else:
            if index in list(team_df.nsmallest(10, stat).index.values.tolist()):
                need_stat.append(False)
            else:
                need_stat.append(True)
    return need_stat


def identifyTeamGoal(row):
    """
    This will identify whether the team is:
        Contending - not interested in most trades (e.g. GSW)
        Buying -  one or two stars away from contending, willing to give up young assets and picks (e.g. POR)
        Rebuilding - trying to develop young talent and accumulate draft picks, willing to give up depth and low tier stars (e.g. NOP)
        Selling - not trying to win, pursuing expiring contracts and draft picks, willing to give up anyone good(e.g. PHO)
    """
    if row["srs"] < -4.5:
        return "selling"
    elif row["srs"] < 0:
        return "rebuilding"
    elif row["srs"] > 4.5:
        return "contending"
    else:
        return "buying"


def splitTeamRow(row, suffix=""):
    """
    This breaks up a row of HTML into a dictionary of stats and their values for that row.
    """
    row_data = {}
    row_data["team_id"] = findBetween(row, "/teams/", "/")
    row_data["name"] = findBetween(row, ".html\">", "</a>")
    columns = row.split("data-stat")[2:]
    for column in columns:
        stat = findBetween(column, "=\"", "\"")
        if stat != "g":
            stat = stat + suffix
        value = findBetween(column, ">", "<")
        if "team_name" not in stat:
            row_data[stat] = value
    return row_data


def getTeamData(source, table_id, suffix=""):
    """
    This splits a table into rows and feeds them into split_team_row to get a dictionary of the data in the row
    Suffix specifies which table this is in, since there are duplicate column names on Basketball-Reference
    """
    data_table = findBetween(source, "<tbody>", "</tbody>", source.find(table_id))
    source_rows = data_table.split("<tr >")[1:]
    rows = []
    for source_row in source_rows:
        row_data = splitTeamRow(source_row, suffix)
        rows.append(row_data)

    return pd.DataFrame(rows).sort_values(by="team_id").set_index("team_id")


def generateStatsDF(url):
    """
    This separates HTML source code into rows and then feeds them into split_player_row to get
    back a dictionary of player stats. It then creates a dataframe from that dictionary and returns it.
    """
    source = getSourceCode(url)
    source_table = findBetween(source, "<tbody>", "</tbody>")
    source_rows = source_table.split("<tr class=\"full_table\" >")[1:]
    rows = []
    for source_row in source_rows:
        row_data = splitPlayerRow(source_row[:source_row.find("</tr>")])
        rows.append(row_data)
    stats_df = pd.DataFrame(rows).sort_values(by="player_id").set_index("player_id")
    return stats_df.apply(pd.to_numeric, errors="ignore")


def splitPlayerRow(row):
    """
    This breaks up a row of HTML into a dictionary of stats and their values for that row.
    """
    row_data = {}
    row_data["player_id"] = findBetween(row, "data-append-csv=\"", "\"")
    row_data["name"] = findBetween(row, row_data["player_id"] + ".html\">", "</a>")
    columns = row.split("data-stat")[3:]
    for column in columns:
        stat = findBetween(column, "=\"", "\"")
        value = findBetween(column, ">", "<")
        if stat not in ("team_id"):
            row_data[stat] = value
    return row_data


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
    print("Total run time:", round(time.time() - start, 3))
