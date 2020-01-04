from pymongo import MongoClient



def mongoSetup():
    '''Initializes a localhost mongoDB, and returns the MongoClient object'''
    db_url = 'mongodb://localhost:27017'
    return(MongoClient(db_url))

def set_splicer(database,set_id,slice_point):
    '''Given a target database of slippi replays, slice the given set at the passed index.
    a slice_point of 4 will split the first 4 games into 1 set and the remainder into another.'''
    new_games = [games for games in database.sets.find({'set_id' : set_id})][0]['game'][slice_point:]
    old_games = [games for games in database.sets.find({'set_id' : set_id})][0]['game'][:slice_point]
    tournament = [games for games in database.sets.find({'set_id' : set_id})][0]['tournament']
    new_set = {'set_id' : str(set_id) + 'a',
               'tournament' : tournament,
               'game' : new_games,
               'flagged' : False}
    database.sets.insert_one(new_set)
    database.sets.update_one({'set_id' : set_id}, { "$set": { "game": old_games } })
    database.sets.update_one({'flagged' : False}, { "$set": { "game": old_games } })
    
    return(None)

client = mongoSetup()
slippi_db = client.slippi_replays

#from visually inspecting the flagged sets, these sets are not tournament sets
sets_to_drop = [17,18,43,130,147,171]

for set_id in sets_to_drop:
    slippi_db.sets.delete_one({"set_id" : set_id})

#Mainstage sets needing to be split
#This is all one-time code
set_splicer(slippi_db,199,4)
set_splicer(slippi_db,200,5)
set_splicer(slippi_db,291,5)

#Shine sets needing to be split
set_splicer(slippi_db,124,5)
set_splicer(slippi_db,56,4)
set_splicer(slippi_db,125,5)
set_splicer(slippi_db,174,4)
set_splicer(slippi_db,178,3)
set_splicer(slippi_db,184,3)
print('Done!')
