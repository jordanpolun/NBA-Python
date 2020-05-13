"""
This looks at all all-star seasons in the 3 point era
Finds the best players from this set based on PER for that season
Continues until all rosters are filled
"""


import time
import urllib.request
import string

def main():
    lines = []
    lines.append("name,salary,minutes.played,hourly.wage\n")
    for letter in string.ascii_lowercase:
        if letter == "x":
            continue
        letter_url = "https://www.basketball-reference.com/players/" + letter + "/"
        letter_source = getSourceCode(letter_url)
        letter_table = findBetween(letter_source, "<tbody>", "</tbody>")
        letter_rows = letter_table.split("<tr >")[1:]
        for letter_row in letter_rows:
            player_ext = findBetween(letter_row, "<a href=\"", "\"")
            player_url = "https://www.basketball-reference.com" + player_ext
            player_source = getSourceCode(player_url)

            # Find player name
            name = findBetween(player_source, "<title>", " Stats")

            # Find total money made in career
            salary_table_after_index = player_source.find("all_all_salaries")
            if salary_table_after_index != -1:
                salary_after_index = player_source.rfind("data-stat=\"salary\"")
                salary = findBetween(player_source, ">$", "</td>", salary_after_index)
                salary_float = float(salary.replace(",", ""))
            else:
                continue

            # Find total minutes played in career
            totals_table_after_index = player_source.find("all_totals")
            if totals_table_after_index != -1:
                total_row = findBetween(player_source, "<tfoot><tr >", "</tr>", totals_table_after_index)
                total_mp = findBetween(total_row, "data-stat=\"mp\" >", "<")
                if len(total_mp) > 0:
                    total_mp_float = float(total_mp)
                else:
                    continue

            if total_mp_float > 0:
                lines.append(name + "," + str(salary_float) + "," + str(total_mp_float) + "," + str(round(
                    salary_float/total_mp_float, 2)) + "\n")

    file = open("salaries.csv", "w+", encoding='utf-8')
    file.writelines(lines)
    file.close()

def getSourceCode(inputURL):
    try:
        webURL = urllib.request.urlopen(inputURL)
        data = webURL.read()
        return data.decode(webURL.headers.get_content_charset(), errors="replace")
    except:
        print("Couldn't connect to " + inputURL)

def findBetween(string, substring_1, substring_2, after_index=0):
    start = string.find(substring_1, after_index) + len(substring_1)
    end = string.find(substring_2, start)
    return string[start: end]


if __name__ == "__main__":
    print("Starting up...")
    start = time.time()
    main()
    print("Run time:", round(time.time() - start, 3))
