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


def wildcard_sim(opt, ot):
    squad = Wildcard(opt, processed_data, optimal_team=ot)
    print('Wildcard simulation complete')
    print('Best team/formation is as follows:')
    Lineup(squad.squad, param=opt).print_lineup()


def substitution_sim(opt, n, ot):
    squad = Substitution(opt, processed_data, n_subs=n, optimal_team=ot)
    player, replacement = squad.extract_subs()
    print('Substitution simulation complete')
    print('\nOptimal subs:')
    for p, r in zip(player, replacement):
        print(p['web_name'], '>', r['web_name'])
    print('\nBest team/formation is as follows:')
    Lineup(squad.squad, param=opt).print_lineup()


opt_param = 'total_points'
num_subs = 4
optimal = False
creds = get_credentials()
if creds:
    processed_data = GetData(creds['user'], creds['pass'], reduce=False, refresh=False).data
    wildcard_sim(opt_param, optimal)
    # substitution_sim(opt_param, num_subs, optimal)
    # Lineup(processed_data.team_list, param=opt_param).print_lineup()

ender = True
