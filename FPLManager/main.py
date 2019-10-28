import csv

from FPLManager.get_data import GetData
from FPLManager.lineup import Lineup
from FPLManager.opt import Substitution
from FPLManager.opt import Wildcard


def get_credentials():
    with open('./data/credentials.csv', "r") as f:
        reader = csv.reader(f, delimiter="\t")
        credentials = []
        for line in reader:
            if ',' in line[0]:
                credentials.append(line[0].split(",")[1])
    if credentials:
        return {'user': credentials[0], 'pass': credentials[1]}
    else:
        return False


def wildcard_sim(opt, budget, want):
    squad = Wildcard(opt, processed_data, budget, desired=want)
    print('Wildcard simulation complete')
    print('Best team/formation is as follows:')
    Lineup(squad.squad, param=opt).print_lineup()


def substitution_sim(opt, budget, n, desired):
    squad = Substitution(opt, processed_data, budget, n, desired)
    player, subs = squad.extract_subs()
    old, new = squad.calculate_improvement()
    print('\n\nSubstitution simulation complete (', opt, '),', sep='')
    print('previous ', opt, ' - ', round(old, 1), '\n', 'new ', opt, ' - ', round(new, 1), sep='')
    print('That\'s an improvement of -', round(new - old, 1))
    print('\nOptimal subs:')
    for p, s in zip(player, subs):
        print(p['web_name'], '>', s['web_name'])
    print('\nBest team/formation is as follows:')
    Lineup(squad.squad, param=opt).print_lineup()


############################
# USEFUL METRICS TO OPTIMISE
# --------------------------
# bonus
# bps
# creativity
# dreamteam_count
# ep_next
# ep_this
# event_points
# form
# goals_scored
# ict_index
# influence
# KPI
# points_per_game
# price_change
# selected_by_percent
# threat
# total_points
# transfers_in
# transfers_in_event
# value_form
# value_season

opt_param = 'ep_next'
num_subs = 1
budget = 99.5
desired = []

creds = get_credentials()
if creds:
    processed_data = GetData(creds['user'], creds['pass'], reduce=False, refresh=False).data
    # wildcard_sim(opt_param, budget, want=desired)
    substitution_sim(opt_param, budget, num_subs, desired)
    # Lineup(processed_data.team_list, param=opt_param).print_lineup()

ender = True
