from slippi import Game
import os
from datetime import datetime, timedelta
from pymongo import MongoClient

def mongoSetup():
    '''Initializes a localhost mongoDB, and returns the MongoClient object'''
    db_url = 'mongodb://localhost:27017'
    return(MongoClient(db_url))

def characters_played(game):
    '''Arguments: py.slippi Game object
       Outputs: List of tuples of characters played in what port. Excludes empty/unused ports'''
    
    character_list = []
    port_counter = 1
    for player in game.start.players:
        if player != None:
                character_list.append([str(player.character).split('.')[1],port_counter])
        port_counter += 1
        
    return(character_list)

def game_length(game):
    '''Arguments: py.slippi Game object
       Outputs: 2-length list containing two datetime objects: the game's start and the game's end'''
    
    game_start = game.metadata.date
    game_duration = round(game.metadata.duration)/60
    game_end = game_start + timedelta(seconds=game_duration)
    
    return([game_start, game_end])

def basic_game_info(game):
    '''Arguments: py.slippi Game object
       Outputs: 2-length list containing the stage the game was played on, and the port number of the winner'''
    
    info_dict = {'Stage' : '',
                 'Winner' : ''}
    
    info_dict['Stage'] = str(game.start.stage).split('.')[1]
    
    port_counter = 1
    for port in game.frames[-1].ports:
        if port != None:
            if port.leader.post.stocks != 0:
                info_dict['Winner'] = port_counter
        port_counter += 1
            
    
    
    return(info_dict)

def replay_parser(directory, tournament=None, stream_filter=None):
    '''For a given directory, search recursively for all .slp files, parse them with the below functions,
    and return a list of dictionaries with each dictionary as specified:
    {game_id, tournament, stream_filter, absolute directory path, 
    game_start, game_end, ports, characters, stage, winner}'''
    
    replay_list = []
    game_id = 0
    #walk the directory
    for subdir, dirs, files in os.walk(directory):
        for file in files:
            #only look at .slp files, then build our dictionary
            if file.endswith('.slp'):
                file_path = os.path.join(subdir, file)
                game = Game(file_path)
                characters = characters_played(game)
                print(characters)
                #if the replay is corrupted such that the character list is empty, skip that file
                if characters != []:
                    gameLength = game_length(game)
                    game_info = basic_game_info(game)
                    replay_list.append({'game_id' : game_id,
                                        'tournament' : tournament,
                                        'stream_filter' : stream_filter,
                                        'file_path' : file_path,
                                        'game_start' : gameLength[0],
                                        'game_end' : gameLength[1],
                                        'port_1' : characters[0][1],
                                        'port_2' : characters[1][1],
                                        'char_1' : characters[0][0],
                                        'char_2' : characters[1][0],
                                        'stage' : game_info['Stage'],
                                        'winner' : game_info['Winner']})
                    game_id += 1
    
    return(replay_list)

def main():
    #initialize the mongo client and database
    client = mongoSetup()
    slippi_db = client.slippi_replays

    #iterate through our replay directory in such a way that our replay parser can tag them correctly
    basedirectory = 'D:/Slippi-ETL/Replays/'
    tourneys = [tourney for tourney in os.listdir(basedirectory)]
    #tourneys = ['The Big House 9']
    for tourney in tourneys:
        stream_filters = [stream_filter for stream_filter in os.listdir(basedirectory + tourney + '/')]
        for stream_filter in stream_filters:
            directory = basedirectory + tourney + '/' + stream_filter + '/'
            print(directory)
            replay_list = replay_parser(directory, tourney, stream_filter)
            slippi_db.replays.insert_many(replay_list)


main()