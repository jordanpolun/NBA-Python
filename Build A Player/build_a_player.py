# Got info from 2kmtcentral from the '20 Current NBA Collection
# Finishing <- Inside Scoring
# Shooting <- Outside Scoring
# Defense <- Defending
# Playmaking <- Playmaking
# Athleticism <- (Athleticism + Rebounding) / 2

import time
import random

def main():
    finishing = ["John Collins", "Pascal Siakam", "DeAaron Fox", "Jimmy Butler", "Russell Westbrook"]
    values_f = [71, 76, 67, 66, 70]
    shooting = ["Duncan Robinson", "Kevin Durant", "Damian Lillard", "Klay Thompson", "Stephen Curry"]
    values_s = [65, 84, 85, 86, 86]
    defense = ["Draymond Green", "Bam Adebayo", "Patrick Beverley", "Rudy Gobert", "Kawhi Leonard"]
    values_d = [86, 70, 79, 84, 82]
    playmaking = ["Kyrie Irving", "James Harden", "Luka Doncic", "Ben Simmons", "LeBron James"]
    values_p = [83, 82, 78, 75, 80]
    athleticism = ["Boban Marjanovic", "Mitchell Robinson", "Anthony Davis", "Zion Williamson", "Giannis Antetokounmpo"]
    values_a = [66, 67.5, 83, 70, 79.5]

    valid_combos = {}
    valid_values = {}
    letters = ["A", "B", "C", "D", "E"]

    for f in range(0, 5):
        for s in range(0, 5):
            for d in range(0, 5):
                for p in range(0, 5):
                    for a in range(0, 5):
                        skills_combo = []
                        skills_combo.append(finishing[f])
                        skills_combo.append(shooting[s])
                        skills_combo.append(defense[d])
                        skills_combo.append(playmaking[p])
                        skills_combo.append(athleticism[a])
                        cost = f + s + d + p + a + 5
                        value = values_f[f] + values_s[s] + values_d[d] + values_p[p] + values_a[a]
                        key = letters[f] + letters[s] + letters[d] + letters[p] + letters[a]
                        if cost == 15:
                            valid_combos[key] = skills_combo
                            valid_values[key] = value

    print(str(len(valid_combos)) + " valid combinations for $15")

    # Sort by best stats
    valid_keys = sorted(valid_values.items(), key=lambda x: x[1], reverse=True)
    valid_keys_8 = valid_keys[:8]

    # Rank breakdown
    breakdown_rank = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
    breakdown_count = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
    for key in valid_keys:
        for char in range(0, 5):
            k = key[0]
            # Add this key's rank to the cell
            breakdown_rank[char][letters.index(k[char])] += (valid_keys.index(key) + 1)
            # Increment this cell's count
            breakdown_count[char][letters.index(k[char])] += 1

    # The cell with the smallest number is the best attribute
    # Find average rank by sum of ranks/count
    print("   F   S   D   P   A  ")
    for row in range(4, -1, -1):
        print("$" + str(row + 1), end=" ")
        for col in range(0, 5):
            breakdown_rank[col][row] = breakdown_rank[col][row] / breakdown_count[col][row]
            print(round(breakdown_rank[col][row]), end=" ")
        print()

    print()



    # Print best 8 teams for bracket
    for key in valid_keys:
        print(key[0], end=" ")
        print(valid_combos[key[0]], end=" ")
        print(" - " + str(key[1]))


    # Assign 4 v 4 teams from best 8 at random
    for _ in range(0, 5):
        random.shuffle(valid_keys_8)
        team_a = []
        team_b = []
        for k in valid_keys_8[:4]:
            team_a.append(k[0])
        for k in valid_keys_8[4:]:
            team_b.append(k[0])

        print()
        print(team_a)
        print(team_b)





if __name__ == "__main__":
    print("Starting up...")
    start = time.time()
    main()
    print("Run time:", round(time.time() - start, 3))
