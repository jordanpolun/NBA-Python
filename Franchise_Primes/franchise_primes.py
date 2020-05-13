"""
This looks at all all-star seasons in the 3 point era
Finds the best players from this set based on PER for that season
Continues until all rosters are filled
"""


import time
import urllib.request
import operator

def main():
    play_index_base_url = "https://www.basketball-reference.com/play-index/psl_finder.cgi?request=1&match=combined&type=totals&per_minute_base=36&per_poss_base=100&lg_id=NBA&is_playoffs=N&year_min=1980&year_max=&franch_id=&season_start=1&season_end=-1&age_min=0&age_max=99&shoot_hand=&height_min=0&height_max=99&birth_country_is=Y&birth_country=&birth_state=&college_id=&draft_year=&is_active=&debut_yr_nba_start=&debut_yr_nba_end=&is_hof=&is_as=Y&as_comp=gt&as_val=1&award=&pos_is_g=Y&pos_is_gf=Y&pos_is_f=Y&pos_is_fg=Y&pos_is_fc=Y&pos_is_c=Y&pos_is_cf=Y&qual=&c1stat=&c1comp=&c1val=&c2stat=&c2comp=&c2val=&c3stat=&c3comp=&c3val=&c4stat=&c4comp=&c4val=&c5stat=&c5comp=&c6mult=&c6stat=&order_by=per&order_by_asc"

    # Each key in this dictionary has a value of a list of player names (their roster)
    teams = {
        "ATL" : {}, "BOS" : {}, "NJN" : {}, "CHA" : {}, "CHI" : {},
        "CLE" : {}, "DAL" : {}, "DEN" : {}, "DET" : {}, "GSW" : {},
        "HOU" : {}, "IND" : {}, "LAC" : {}, "LAL" : {}, "MEM" : {},
        "MIA" : {}, "MIL" : {}, "MIN" : {}, "NOH" : {}, "NYK" : {},
        "OKC" : {}, "ORL" : {}, "PHI" : {}, "PHO" : {}, "POR" : {},
        "SAC" : {}, "SAS" : {}, "TOR" : {}, "UTA" : {}, "WAS" : {}
    }

    # For keeping track of who we already used
    used_players = []

    # For each of the first 1000 best seasons
    offset = 0
    keep_going = True
    while keep_going:
        play_index_url = play_index_base_url + "=&offset=" + str(offset)
        play_index_source = getSourceCode(play_index_url)
        play_index_table = findBetween(play_index_source, "<tbody>", "</tbody>")
        play_index_rows = play_index_table.split("<tr >")[1:]
        if len(play_index_rows) <= 0: # If we couldn't find anyone (MEM), break out
            break
        for player_row in play_index_rows:
            player_url = findBetween(player_row, "<a href=\"", "\">")
            player_name = findBetween(player_row, ".html\">", "</a>")
            player_stat = findBetween(player_row, "data-stat=\"per\" >", "</td>")

            # If we already used this player, don't add them again
            if player_name not in used_players:
                used_players.append(player_name) # Add them to the list of used players
                print(player_name)

                # Find which teams the player played for
                player_source = getSourceCode("https://www.basketball-reference.com" + player_url)
                player_per_game_table = findBetween(player_source, "<tbody>", "</tbody>")
                player_per_game_rows = player_per_game_table.split("<tr")[1:]
                teams_played_for = [] # Keep track of unique teams
                for per_game_row in player_per_game_rows:
                    team_id = findBetween(per_game_row, "/teams/", "/")

                    # If we haven't already used this team...
                    if "full_table" not in team_id and \
                            "Did Not Play" not in per_game_row and \
                            team_id not in teams_played_for:
                        teams_played_for.append(team_id)

                        # Figure out what current day team this is, if any
                        # Make sure this team doesn't already have this player
                        if team_id in teams.keys() and \
                                player_name not in teams[team_id] and \
                                len(teams[team_id]) < 15:
                            print("\t" + team_id)
                            teams[team_id][player_name] = float(player_stat)
                        else:
                            team_source = getSourceCode("https://www.basketball-reference.com/teams/" + team_id + "/")
                            current_team_id = findBetween(team_source, "/teams/", "/")
                            # Some teams just disappeared like the WSC
                            if current_team_id in teams.keys() and \
                                    player_name not in teams[current_team_id] and \
                                    len(teams[current_team_id]) < 15:
                                print("\t" + current_team_id)
                                teams[current_team_id][player_name] = float(player_stat)

        # Keep looking at players if not all rosters are full
        keep_going = False
        for team in teams.keys():
            if len(teams[team]) < 15:
                print(team + " is not full!")
                keep_going = True
                offset += 100
                break

    teams_totals = {}
    for team in teams.keys():
        total = 0
        for player in teams[team].keys():
            total += teams[team][player]
        teams_totals[team] = total
    teams_totals = sorted(teams_totals.items(), key=operator.itemgetter(1), reverse=True)

    for tup in teams_totals:
        team = tup[0]
        print(team + ":")
        for player in teams[team].keys():
            print("\t" + player)

    print("Looked at first " + str(offset) + " seasons.")


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
