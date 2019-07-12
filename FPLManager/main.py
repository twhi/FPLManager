import csv

from FPLManager.get_data import GetData
from FPLManager.lineup import Lineup
from FPLManager.opt import Wildcard
from FPLManager.opt import Substitution


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


def wildcard_sim(opt, ot):
    wc = Wildcard(opt, processed_data, optimal_team=ot)
    print('Wildcard simulation complete')
    print('Best team/formation is as follows:')
    Lineup(wc.squad, param=opt).print_lineup()


def simulation_sim(opt, n, ot):
    sub = Substitution(opt, processed_data, n_subs=n, optimal_team=ot)
    print('\n###########################')
    print('\nSub simulation complete. Optimal subs:')
    for substitution in sub.best_subs:
        print(substitution)
    print('\nBest team/formation is as follows:')
    Lineup(sub.best_team, param=opt).print_lineup()


opt_param = 'points_per_game'
num_subs = 2
optimal = False
creds = get_credentials()
if creds:
    processed_data = GetData(creds['user'], creds['pass'], reduce=False, refresh=True).data
    wildcard_sim(opt_param, optimal)
    # simulation_sim(opt_param, num_subs, optimal)
    # Lineup(processed_data.team_list, param=opt_param).print_lineup()

ender = True
