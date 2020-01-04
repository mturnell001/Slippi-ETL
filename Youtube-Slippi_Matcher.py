from pymongo import MongoClient
debug = False

def mongoSetup():
    '''Initializes a localhost mongoDB, and returns the MongoClient object'''
    db_url = 'mongodb://localhost:27017'
    return(MongoClient(db_url))

#setting up variables
client = mongoSetup()
replay_db = client.slippi_replays
yt_db = client.slippi_vids
vid_collection = yt_db.videos
set_collection = replay_db.sets
tournaments = [ 'Smash Summit 8' ,
                    'Shine 2019' ,
                    'Mainstage']
unmatched_videos = []

#step through each tournament
for tournament in tournaments:
    #step through each video for that tournament
    for video in vid_collection.find({'tournament' : tournament}):
        if debug: print(video['vid-id'])
        if debug: print(video['char1'],video['char2'])
        matched_flag = False
        exact_matches = []
        vid_id = video['vid-id']
        #in case the scraping failed
        if len(video['char1']) == 0 or len(video['char2']) == 0:
            print('EMPTY CHARACTER ARRAY')
            continue
        #local variable assignment
        char1_vidlist = video['char1']
        char2_vidlist = video['char2']
        #step through each set for the tournament
        for set_ in set_collection.find({'tournament' : tournament}):
            set_id = set_['set_id']
            char1_setlist = []
            char2_setlist = []
            #step through each game in the set and collect a list of the characters played
            for game in set_['game']:
                if game['char_1'] not in char1_setlist:
                    char1_setlist.append(game['char_1'])
                if game['char_2'] not in char2_setlist:
                    char2_setlist.append(game['char_2'])
            #if our list of characters from the video title is > 1, look for exact match
            if len(char1_vidlist) > 1 or len(char2_vidlist) > 1:
                if (((char1_vidlist == char1_setlist) and (char2_vidlist == char2_setlist))
                or ((char1_vidlist == char2_setlist) and (char2_vidlist == char1_setlist))):
                    if debug: print(f"Exact match between set {set_id} and video {vid_id}")
                    matched_flag = True
                    exact_matches.append(set_id)
            #if the set we're looking at only had 1 character played per player,
            #and our video has 1 character per player, look for an exact match
            elif (len(char1_vidlist) == 1 and len(char2_vidlist) == 1 and 
                    len(char1_setlist) == 1 and len(char2_setlist) == 1):
                if (((char1_vidlist == char1_setlist) and (char2_vidlist == char2_setlist))
                or ((char1_vidlist == char2_setlist) and (char2_vidlist == char1_setlist))):
                    if debug: print(f"Exact 1 length match between set {set_id} and video {vid_id}")
                    matched_flag = True
                    exact_matches.append(set_id)
            #else, just see if the video list is in the characters played list
            elif (((char1_vidlist[0] in char1_setlist) and (char2_vidlist[0] in char2_setlist))
                or ((char1_vidlist[0] in char2_setlist) and (char2_vidlist[0] in char1_setlist))):
                    matched_flag = True
                    #if we couldn't do any exact matches, this 'looser' match is fine
                    if exact_matches == []:
                        if debug: print(f"Loose match between set {set_id} and video {vid_id}")
                        exact_matches.append(set_id)
        #if we only found one match, mark it as a confident match, otherwise don't
        if len(exact_matches) == 1:
            if debug: print("confident match")
            vid_collection.update_one({'vid-id' : vid_id}, { "$set" : {"matched_sets" : exact_matches}})
            vid_collection.update_one({'vid-id' : vid_id}, { "$set" : {"confident" : True}})
        else:
            if debug: print("one of these...")
            vid_collection.update_one({'vid-id' : vid_id}, { "$set" : {"matched_sets" : exact_matches}})
            vid_collection.update_one({'vid-id' : vid_id}, { "$set" : {"confident" : False}})
        #if we didn't find a match, mark it
        if not matched_flag: unmatched_videos.append(vid_id)

print(unmatched_videos)