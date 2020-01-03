from slippi import Game
from datetime import datetime, timedelta
from pymongo import MongoClient
from pprint import pprint

#DEBUG FLAG
debug = True

def mongoSetup():
    '''Initializes a localhost mongoDB, and returns the MongoClient object'''
    db_url = 'mongodb://localhost:27017'
    return(MongoClient(db_url))

def set_collation(database, tournaments):
    '''Given a mongo database of slippi replays and a list of tournaments,
    sort through the games and naively collate them into a list of sets'''
    #initialize list of sets, and set-id counter
    sets = []
    set_id = 0
    prev_char_1 = None
    prev_char_2 = None
    for tournament in tournaments:
        for replay in database.replays.find({'tournament' : tournament}):
            #this if will only be True on the first game of a tournament, so we don't need other checks
            if prev_char_1 == None and prev_char_2 == None:
                games = []
                games.append(replay)
                set_ = {'set_id' : set_id,
                        'tournament' : tournament,
                        'game' : games}
                #store current game data as previous for comparison in next iteration
                prev_char_1 = replay['char_1']
                prev_char_2 = replay['char_2']
                prev_port_1 = replay['port_1']
                prev_port_2 = replay['port_2']
                prev_game_end = replay['game_end']
            else:
                #DEBUG PRINT
                if debug:
                    print('Prev game end :' +str(prev_game_end))
                    print('Game start :' +str(replay['game_start']))
                
                #store the current in-use ports for easier comparison
                ports = [replay['port_1'], replay['port_2']]
                chars = [replay['char_1'], replay['char_2']]
                #DEBUG PRINT
                if debug:
                    if ((replay['game_start'] - prev_game_end >= timedelta(minutes=4))): 
                        print('New set due to time')
                    
                #if our games start more than 4 minutes after the last game ended, assume it's a new set
                # or if one of the ports change
                # or if both of the characters change
                if ((replay['game_start'] - prev_game_end >= timedelta(minutes=4))
                    or (prev_port_1 not in ports) or (prev_port_2 not in ports)
                    or ((prev_char_1 != chars[0]) and (prev_char_2 != chars[1]))):
                    sets.append(set_)
                    set_id += 1
                    games = []
                
                #append the replay info to the set's game list
                games.append(replay)
                set_ = {'set_id' : set_id,
                        'tournament' : tournament,
                        'game' : games}
                
                #store current game data as previous for comparison in next iteration
                prev_char_1 = replay['char_1']
                prev_char_2 = replay['char_2']
                prev_port_1 = replay['port_1']
                prev_port_2 = replay['port_2']
                prev_game_end = replay['game_end']
            #DEBUG PRINT
            if debug:
                print(set_['set_id'])
                print(replay['char_1'], replay['port_1'])
                print(replay['char_2'], replay['port_2'])

    #if we leave the loop with an unappended set, append the set here
    sets.append(set_)
    
    return(sets)
        
def naive_set_cleanup(sets):
    '''Given a list of sets collated, run additional logic to remove some warmup games, and also
    flag sets that the logic could not clean up but that it recognizes
    as abnormally formatted or sized. Then, return the collated and flagged sets'''
    #This is the 'naive' logic to do basic cleanup and flag some sets
    #iterate over sets in reverse order, due to how python resolves list-removal
    for set_ in reversed(sets):
        #most sets are best of 5, so if we have exactly 6 games it is safe to assume the first one
        #is a warmup, so we should drop it.
        if len(set_['game']) == 6:
            del set_['game'][0]
            set_['flagged']=False
            #DEBUG PRINT
            if debug: print(set_['set_id'], 'removed handwarmer from 6 game set')
        #if the set is still too long, flag it. Otherwise mark it as fine
        elif len(set_['game']) > 5:
            set_['flagged']=True
            #DEBUG PRINT
            if debug: print(set_['set_id'], 'flagged a set')
        #if the set is only 1 game, drop the set from the list
        elif len(set_['game']) == 1:
            sets.remove(set_)
            next 
            #DEBUG PRINT
            if debug: print('removed 1 game set')
        else:
            set_['flagged']=False

    return(sets)


def flagged_set_cleanup(sets):
    '''Given a list of sets, look at the flagged sets with deeper (and slower) parsing than
    naive_set_cleanup. Returns a modified list of sets.'''

    #iterate through the flagged sets and work additional logic to cull games
    for set_ in sets:
        if set_['flagged'] == True:
            if debug: print(f"Looking at set {set_['set_id']}")
            for index in reversed(set_['game']):
                if debug: print(f"Looking at game {index['game_id']}")
                if warmup_detection(Game(index['file_path'])):
                    set_['game'].remove(index) 
                    if debug: print(f"removed game id {index['game_id']} from set {set_['set_id']}")

    return(sets)


def warmup_detection(game):
    '''For a given slippi Game object, iterate through the frames to detect if it is a warmup game
    based on % dealt and # of self-destructs'''
    #initialize some empty lists to collect data in
    damageTaken = [0,0]
    self_destruct_count = [0,0]
    ports_in_use = ['','']
    
    #if the game was quit out of instead of ending normally, return True
    if game.end.lras_initiator != None:
        if debug: print('Game was LRAS')
        return True
    #look through the ports in the replay to see which ports are in use
    port_counter = 0
    for port in game.frames[0].ports:
        if port != None:
            if ports_in_use[0] == '':
                ports_in_use[0] = port_counter
            else:
                ports_in_use[1] = port_counter
        port_counter += 1
    if debug: print(ports_in_use)


    for i in range(len(game.frames)):
        #look for when a stock is lost, then rewind a frame to collect the % taken for that stock
        #if the stock is lost without taking damage, count it as a self-destruct
        #do this for both ports in use
            if (game.frames[i].ports[ports_in_use[0]].leader.post.stocks < 
                game.frames[i-1].ports[ports_in_use[0]].leader.post.stocks):
                dmg_taken = game.frames[i-1].ports[ports_in_use[0]].leader.post.damage
                if dmg_taken == 0:
                    self_destruct_count[0] += 1
                damageTaken[0] += dmg_taken

            if (game.frames[i].ports[ports_in_use[1]].leader.post.stocks < 
                game.frames[i-1].ports[ports_in_use[1]].leader.post.stocks):
                dmg_taken = game.frames[i-1].ports[ports_in_use[1]].leader.post.damage
                if dmg_taken == 0:
                    self_destruct_count[0] += 1
                damageTaken[0] += dmg_taken


    if damageTaken[0] + damageTaken[1] <= 100:
        if debug: print('warmup due to %')
        return True
    elif self_destruct_count[0] >= 3 or self_destruct_count[1] >= 3:
        if debug: print('warmup due to SDs')
        return True
    else:
        return False
    

def main():
    client = mongoSetup()

    slippi_db = client.slippi_replays

    tournaments = [ 'Smash Summit 8' ,
                    'Shine 2019 Top 48' ,
                    'Mainstage' ,
                    'The Big House 9']

    sets = set_collation(slippi_db, tournaments)
    #cull games based on set length
    sets = naive_set_cleanup(sets)
    #DEBUG step
    slippi_db.partial_clean.insert_many(sets)
    #look with deeper logic for handwarmers
    sets = flagged_set_cleanup(sets)
    #after deeper logic, cull games based on set length again
    clean_sets = naive_set_cleanup(sets)
    slippi_db.sets.insert_many(clean_sets)

main()
