# -*- coding: utf-8 -*-

import requests
import json
import getpass
import os

###########################################################################################

def _get_player_position(position_code):
    if position_code == 1:
        return 'G'
    elif position_code == 2:
        return 'D'
    elif position_code == 3:
        return 'M'
    elif position_code == 4:
        return 'F'

def _get_player_data_from_id(master_table, player_id):
    player_dict = next((item for item in master_table if item["id"] == player_id), False)
    if player_dict:
        player_data = {
                'id': player_dict['id'],
                'name': player_dict['web_name'],
                'form': player_dict['form'],
                'price': player_dict['now_cost']/10,
                'position': _get_player_position(player_dict['element_type'])
                }
    return player_data

def construct_session_payload(session, username, password):
    url_home = 'https://fantasy.premierleague.com/'
    session.get(url_home)
    csrftoken = session.cookies['csrftoken']
    return {
        'csrfmiddlewaretoken': csrftoken,
        'login': username,
        'password': password,
        'app': 'plfpl-web',
        'redirect_uri': 'https://fantasy.premierleague.com/a/login'
    }

def log_into_fpl(session, payload):     
    login_url = 'https://users.premierleague.com/accounts/login/'
    status = session.post(login_url, data = payload)
    return status

def log_out_of_fpl(session, payload):
    logout_url = 'https://users.premierleague.com/accounts/logout/?redirect_uri=https://fantasy.premierleague.com/&app=plfpl-web'
    status = session.post(logout_url, data = payload)
    if not status.status_code == 200:
        print('Script completed, but there was an issue logging out. Status code - ' + str(status.status_code))

def get_team_data(session, account_id):
    team_data_url_template = 'https://fantasy.premierleague.com/drf/my-team/[account_id]/'
    team_data_url = team_data_url_template.replace('[account_id]', str(account_id))
    team_data_s = session.get(team_data_url).text
    return json.loads(team_data_s)['picks']

def get_master_data(session):
    master_table_s = session.get('https://fantasy.premierleague.com/drf/elements').text 
    return json.loads(master_table_s)

def _get_n_game_average_difficulty(number_games, fixtures_data):
    sum_difficulty = 0
    for i in range(0, number_games):
        sum_difficulty += fixtures_data[i]['difficulty']
    return round(sum_difficulty / (number_games), 1)

def _calculate_game_difficulty(player_id):
    player_url = player_url_template.replace('[PLAYER_ID]', str(player_id))
    fixtures_data = json.loads(session.get(player_url).text)['fixtures']
    three_game_difficulty = _get_n_game_average_difficulty(3, fixtures_data)
    five_game_difficulty = _get_n_game_average_difficulty(5, fixtures_data)
    return {'diff_3':three_game_difficulty, 'diff_5':five_game_difficulty}
    

def construct_team_list(master_table, master_team_list, price_data):
    team_list = []
    for player in master_team_list:
        player_data = _get_player_data_from_id(master_table, player['element'])
        
        price_change = _player_data_from_name(price_data, player_data['name'])
        player_data['price_change'] = price_change  
        
        game_difficulty = _calculate_game_difficulty(player_data['id'])
        player_data['difficulty'] = game_difficulty  
        
        team_list.append(player_data)
    return team_list 

def get_unique_account_data(session):
    data = json.loads(session.get('https://fantasy.premierleague.com/drf/bootstrap-dynamic').text)
    account_data = {
            'unique_id':data['entry']['id'],
            'bank': data['entry']['bank']/10,
            'total_balance': data['entry']['value']/10
            }
    return account_data
    

###########################################################################################

def get_price_data(url_template):
    row_num = 100
    url = url_template.replace('[row_num]',str(row_num))
    master_price_data = json.loads(session.get(url).text)
    
    while len(master_price_data['aaData']) == 0:
        url = url_template.replace('[row_num]',str(row_num))
        master_price_data = json.loads(session.get(url).text)
        row_num += 1        
    return master_price_data['aaData']

def _player_data_from_name(price_data, name):
    for player in price_data:
        if player[1] == name:
            price_change = player[14]
            return price_change
    return False
    

def find_alternative_players():
    for player in team_list:
        if player['price_change'] in ['-2','-3']:
            suggestions = _get_suggestions(master_table, price_data, player)
            player['suggestions'] = suggestions

def _get_suggested_player_data(player):
    player_dict = next((item for item in master_table if item["web_name"] == player[1]), False)
    return player_dict

def _get_suggestions(master_table, price_data, player):
    suggestions = []
    current_player_position = player['position']
    current_player_price = player['price']
    current_player_form = player['form']
    available_money = account_data['bank']
    
    for suggested_player in price_data:
        suggested_player_position = suggested_player[3]
        suggested_player_price_change = suggested_player[14]
        suggested_player_price = suggested_player[6]
        
        # does the current player play in the same position?
        if not suggested_player_position == current_player_position:
            continue
        
        # is the current player likely to go up in value this week?
        if not int(suggested_player_price_change) >= 2:
            continue
        
        # do i have enough money to buy this player?
        if not float(suggested_player_price) < (current_player_price + available_money):
            continue
        
        # get more data on this player
        suggested_player_data = _get_suggested_player_data(suggested_player)
        suggested_player_name = suggested_player_data['web_name']
        suggested_player_form = suggested_player_data['form']
        suggested_player_cost = suggested_player_data['now_cost']/10
        suggested_player_id = suggested_player_data['id']
        
        # is this player on better form than my current player
        if suggested_player_data['form'] > current_player_form:   
            game_difficulty = _calculate_game_difficulty(suggested_player_id)
            suggestions.append({'name':suggested_player_name,'form':suggested_player_form,'price':suggested_player_cost,'difficulty':game_difficulty})
    return suggestions

###########################################################################################

def print_data(team_list):
    print('###################################')
    print('TEAM PRICE CHANGE INFO\n')
    for player in team_list:
        print('\n###################################')
        print(player['name'])
        print('    Price change probability - ' + player['price_change'])
        print('    Player form - ' + player['form'])
        if 'suggestions' in player:
            if len(player['suggestions']) > 0:
                print('    Player price is likely to depreciate, here are some alternatives:')
                for suggestion in player['suggestions']:
                    print('        ' + suggestion['name'] + ', form ' + str(suggestion['form']), ', price £' + str(suggestion['price']) + ', 3 game difficulty - ' + str(suggestion['difficulty']['diff_3']) + ', 5 game difficulty - ' + str(suggestion['difficulty']['diff_5']))                                            
            else:
                print('    Player is likely to depreciate, but no suitable alternatives found.')

#######################################
# DO FPL STUFF 
username = input('Please enter your FPL username: ')
password = getpass.getpass('Please enter your FPL password: ')
price_url_template = 'http://www.fplstatistics.co.uk/Home/AjaxPricesCHandler?iselRow=[row_num]&_=99999999999999'   
player_url_template = 'https://fantasy.premierleague.com/drf/element-summary/[PLAYER_ID]'
 
session = requests.Session()    
payload = construct_session_payload(session, username, password)
status = log_into_fpl(session, payload)

if status.status_code == 200:
    print('Successfully logged in!')
    account_data = get_unique_account_data(session)
    master_team_list = get_team_data(session, account_data['unique_id'])
    master_table = get_master_data(session)
    price_data = get_price_data(price_url_template)
    
    team_list = construct_team_list(master_table, master_team_list, price_data)    
    log_out_of_fpl(session, payload)
    find_alternative_players()
    
    # MUST GO AT THE END
    print_data(team_list)
else:
    print('Error connecting to FPL. Please check your credentials and try again') 
	
os.system("pause")

# TODO: figure out a way to make cookies persist between runs. Pretty useful
# information here: https://stackoverflow.com/questions/13030095/how-to-save-requests-python-cookies-to-a-file