"""
This looks at all 3 time allstars
Groups by first name to form teams of at least 5
"""

import time
import urllib.request

def main():
    # All 2-time all stars
    play_index_base_url = "https://www.basketball-reference.com/play-index/psl_finder.cgi?request=1&match=combined&type=totals&per_minute_base=36&per_poss_base=100&season_start=1&season_end=-1&lg_id=NBA&age_min=0&age_max=99&is_playoffs=N&height_min=0&height_max=99&birth_country_is=Y&as_comp=gt&as_val=2&pos_is_g=Y&pos_is_gf=Y&pos_is_f=Y&pos_is_fg=Y&pos_is_fc=Y&pos_is_c=Y&pos_is_cf=Y&order_by=per"

    # All players who have started at least 10 games in their career
    play_index_base_url = "https://www.basketball-reference.com/play-index/psl_finder.cgi?request=1&match=combined&type=totals&per_minute_base=36&per_poss_base=100&season_start=1&season_end=-1&lg_id=NBA&age_min=0&age_max=99&is_playoffs=N&height_min=0&height_max=99&birth_country_is=Y&as_comp=gt&as_val=0&pos_is_g=Y&pos_is_gf=Y&pos_is_f=Y&pos_is_fg=Y&pos_is_fc=Y&pos_is_c=Y&pos_is_cf=Y&c1stat=gs&c1comp=gt&c1val=10&order_by=per"

    # Required to look at multiple pages
    play_index_base_url += "&order_by_asc=&offset="
    offset = 0

    # Data structure outline (2d dict)
    # { TEAM_NAME : { PLAYER_NAME : WIN_SHARES } }
    first_name_teams = {}
    last_name_teams = {}
    full_source = ""

    while "Sorry, there are no results that match your search." not in full_source:
        full_source = getSourceCode(play_index_base_url + str(offset))
        table_source = findBetween(full_source, "<tbody>", "</tbody>")

        rows = table_source.split("<tr ><th scope=\"row\"")[1:]
        for row in rows:
            full_name = findBetween(row, "data-stat=\"player\" csk=\"", "\"")
            first_name = full_name[full_name.find(",") + 1:]
            last_name = full_name[:full_name.find(",")]
            per = float(findBetween(row, "data-stat=\"per\" >", "<"))

            if first_name in first_name_teams.keys() and len(first_name_teams[first_name]) < 10:
                first_name_teams[first_name][full_name] = per
            else:
                first_name_teams[first_name] = { full_name : per }

            if last_name in last_name_teams.keys() and len(last_name_teams) < 10:
                last_name_teams[last_name][full_name] = per
            else:
                last_name_teams[last_name] = { full_name : per }

        offset += 100

    # Narrow to only teams with at least 5 players
    valid_first_name_teams = {}
    for t in first_name_teams.keys():
        if (len(first_name_teams[t]) >= 5):
            valid_first_name_teams[t] = first_name_teams[t]

    valid_last_name_teams = {}
    for t in last_name_teams.keys():
        if (len(last_name_teams[t]) >= 5):
            valid_last_name_teams[t] = last_name_teams[t]

    # Find scores of each team by summing career win shares of starting 5
    first_name_team_scores = {}
    for t in valid_first_name_teams.keys():
        starting_5 = {k: valid_first_name_teams[t][k] for k in list(valid_first_name_teams[t])[:5]}
        team_score = sum(starting_5.values())
        first_name_team_scores[t] = team_score

    last_name_team_scores = {}
    for t in valid_last_name_teams.keys():
        starting_5 = {k: valid_last_name_teams[t][k] for k in list(valid_last_name_teams[t])[:5]}
        team_score = sum(starting_5.values())
        last_name_team_scores[t] = team_score

    # Sort teams by their score best -> worst
    first_name_team_scores = {k: first_name_team_scores[k] for k in sorted(first_name_team_scores, key=first_name_team_scores.get, reverse=True)}
    last_name_team_scores = {k: last_name_team_scores[k] for k in sorted(last_name_team_scores, key=last_name_team_scores.get, reverse=True)}

    # Print teams and rosters neatly
    for t in first_name_team_scores:
        print(t + " --- " + str(first_name_team_scores[t]))
        for p in valid_first_name_teams[t].keys():
            print("\t" + p + " : " + str(valid_first_name_teams[t][p]))
        print()

    for t in last_name_team_scores:
        print(t + " --- " + str(last_name_team_scores[t]))
        for p in valid_last_name_teams[t].keys():
            print("\t" + p + " : " + str(valid_last_name_teams[t][p]))
        print()






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
