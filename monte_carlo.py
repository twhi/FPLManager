import random

main_data = m_data.copy()

def filter_list_by_position(data, position):
    outlist = []
    for player in data:
        if player['position'] == position:
            outlist.append(player)
    return outlist
            

def pick_team(gk, df, md, fw):
    goalkeepers = pick_players(2, gk)
    defenders = pick_players(5, df)
    midfielders = pick_players(5, md)
    forwards = pick_players(3, fw)
    return goalkeepers + defenders + midfielders + forwards
    
    
def pick_players(num, dataset):
    data = dataset.copy()
    selected = 0
    player_list = []
    while selected < num:
        index = random.randrange(len(data))
        elem = data[index]
        del data[index]
        player_list.append(elem)
        selected += 1
    return player_list


gk = filter_list_by_position(main_data, 'G')
df = filter_list_by_position(main_data, 'D')
md = filter_list_by_position(main_data, 'M')
fw = filter_list_by_position(main_data, 'F')

team_list = []

for i in range(1000):
    final_team = pick_team(gk, df, md, fw)
    team_list.append(final_team)
    
ender = True
