from pymongo import MongoClient
debug = False


def mongoSetup():
    '''Initializes a localhost mongoDB, and returns the MongoClient object'''
    db_url = 'mongodb://localhost:27017'
    return(MongoClient(db_url))


def char_standardizing(collection, fields=[]):
    '''For a given collection, parse the given fields and change them to the correct alias.'''
    #a dictionary of character name aliases that video titles may use
    #will be used to standardize character names
    #if a character is not in the list, look for exact match only
    char_alias = {'CAPTAIN_FALCON' : ['Captain Falcon', 'C. Falcon', 'Capt. Falcon', 'CF', 'C.F', 'Falcon'],
                    'DONKEY_KONG' : ['DONKEY KONG','DK','D. Kong'],
                    'GAME_AND_WATCH' : ['Mr. Game and Watch', 'Mr Game and Watch', 'Gnw', 
                                        'G&W', 'Mr G&W', 'Mr. G&W', 'Mr Gnw', 'Mr. Gnw', 
                                        'Game and watch', 'Game & Watch', 'Mr. Game & Watch', 'Mr Game & Watch'],                
                    'MEWTWO' : ['M2','Mew2'],                
                    'ICE_CLIMBERS' : ['Ice Climbers', 'IC', 'ICs', 'ICies', 'Climbers'],
                    'JIGGLYPUFF' : ['Puff', 'Jiggly'],
                    'YOUNG_LINK' : ['Y. Link', 'YLink', 'Y Link', 'Young Link', 'Yink'],
                    'DR_MARIO' : ['Dr. Mario', 'Dr Mario', 'Doc', 'Doc Mario'],
                    'GANONDORF' : ['Ganon']}
    slippi_char_names = ['CAPTAIN_FALCON',
                    'DONKEY_KONG',
                    'FOX',
                    'GAME_AND_WATCH',
                    'KIRBY',
                    'BOWSER',
                    'LINK',
                    'LUIGI',
                    'MARIO',
                    'MARTH',
                    'MEWTWO',
                    'NESS',
                    'PEACH',
                    'PIKACHU',
                    'ICE_CLIMBERS',
                    'JIGGLYPUFF',
                    'SAMUS',
                    'YOSHI',
                    'ZELDA',
                    'SHEIK',
                    'FALCO',
                    'YOUNG_LINK',
                    'DR_MARIO',
                    'ROY',
                    'PICHU',
                    'GANONDORF']

    for x in collection.find({}):
        #iterate over the given fields in the given collection
        for field in fields:
            if debug: print(x[field])
            char = x[field]
            fixed_char_names = []
            #if the video title characters has a '/' or a ',', indicating multiple characters, split them into a list
            if '/' in char:
                char_names = char.split('/')
            elif ',' in char:
                char_names = char.split(',')
            #otherwise, create a 1 element list
            else:
                char_names = [char]
            if debug: print(char_names)
            #for each string in our list, check it against our alias list and the list of slippi names
            #if there's a match, update the collection field to the 'proper' name
            for char_name in char_names:
                for alias in char_alias:
                    if char_name.lower() in [x.lower() for x in char_alias[alias]]:
                        fixed_char_names.append(alias)
                for slippi_name in slippi_char_names:
                    if char_name.lower() in slippi_name.lower():
                        fixed_char_names.append(slippi_name)
            if debug: print(fixed_char_names)
            if not debug: collection.update_one({'vid-id' : x['vid-id']}, { "$set" : {field : fixed_char_names}})



def main():
    client = mongoSetup()
    yt_db = client.slippi_vids

    video_collection = yt_db.videos
    fields = ['char1','char2']

    char_standardizing(video_collection,fields)



main()