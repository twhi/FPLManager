import csv

from FPLManager.get_data import GetData
from FPLManager.lineup import Lineup
from FPLManager.opt import Opt


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


def opt(opt_p, budget, desired, remove, n=None):
    if n:
        squad = Opt.transfer_simulation(opt_p, processed_data, n, budget, desired, remove)
    else:
        squad = Opt.wildcard_simulation(opt_p, processed_data, budget, desired, remove)

    if squad.prob.status == 1:
        player, subs = squad.extract_subs()
        old, new = squad.calculate_improvement()
        print('\n\nSubstitution simulation complete (', opt_p, '),', sep='')
        print('previous ', opt_p, ' - ', round(old, 1), '\n', 'new ', opt_p, ' - ', round(new, 1), sep='')
        print('That\'s an improvement of -', round(new - old, 1))
        print('\nOptimal subs:')
        for p, s in zip(player, subs):
            print(p['web_name'], '>', s['web_name'])
        print('\nBest team/formation is as follows:')
        Lineup(squad.squad, param=opt_p).print_lineup()
    else:
        print('Unable to find solution with specified parameters. Simulation status code:', squad.prob.status)


params = ['bonus',
          'bps',
          'creativity',
          'dreamteam_count',
          'ep_next',
          'ep_this',
          'event_points',
          'form',
          'goals_scored',
          'ict_index',
          'influence',
          'KPI',
          'points_per_game',
          # 'price_change',
          'selected_by_percent',
          'threat',
          'top_50_count',
          'total_points',
          'transfers_in',
          'transfers_in_event',
          'value_form',
          'value_season',
          ]

opt_param = 'ep_next'
num_subs = 1
desired = []
remove = []

creds = get_credentials()
if creds:
    processed_data = GetData(creds['user'], creds['pass'], reduce=False, refresh=False).data
    budget = round(processed_data.account_data['total_balance'], 1)

    # transfer sim
    opt(opt_param, budget, desired, remove, num_subs)

    # wildcard sim
    # opt(opt_param, budget, desired, remove)

ender = True
