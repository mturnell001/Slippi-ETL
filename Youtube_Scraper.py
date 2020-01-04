from splinter import Browser
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import time
from pymongo import MongoClient

def mongoSetup():
    '''Initializes a localhost mongoDB, and returns the MongoClient object'''
    db_url = 'mongodb://localhost:27017'
    return(MongoClient(db_url))

def yt_playlist_scraper(playlist):
    '''For a given youtube playlist, with the URL being of the 1st video of the playlist,
    scrape all the video titles in the playlist into a list, which is then returned'''
    with Browser('chrome', headless=True) as browser:

        url = playlist
        browser.visit(url)
        time.sleep(3)
        html = browser.html
        soup = bs(html, "html.parser")

    title_list = []
    for tag in soup.find_all("span", id='video-title', class_="ytd-playlist-panel-video-renderer"):
        if tag.text not in title_list:
            title_list.append(tag.text.strip())
            
    return(title_list)
    
def title_Parser(video_titles):
    '''Given a list of well-behaved YouTube SSBM video titles, parse the titles into
    characters and players, then return a list of dictionaries with that information'''
    video_info = []
    vid_id = 0
    for key in video_titles:
        for title in video_titles[key]:
            players = title.split('-', 1)[0]
            try:
                chars = title.split('-',1)[1].split('|')[1]
            except:
                continue
            player1 = players.split('vs')[0]
            char1 = chars.split('vs')[0]
            try:
                player2 = players.split('vs')[1]
                char2 = chars.split('vs')[1]
            except:
                continue
            
            video_info.append({'vid-id' : vid_id,
                               'tournament' : key,
                               'player 1' : player1.strip(),
                               'player 2' : player2.strip(),
                               'char1' : char1.strip(),
                               'char2' : char2.strip()})
            vid_id += 1
    return(video_info)
    
def main():
    #set up mongo client and db to receive info
    client = mongoSetup()
    video_db = client.slippi_vids

    #list of youtube playlists to scrape
    playlists = {'Smash Summit 8' : 'https://www.youtube.com/watch?v=ccfhiugzmNw&list=PLCR3KcbG-XGt0YNADoCoGSFwG6X0edPc9&index=1',
             'Shine 2019' : 'https://www.youtube.com/watch?v=n41vnp6Uy-w&list=PLCR3KcbG-XGvpRJx_ZV95_ciJJHdzTYkH&index=1',
             'Mainstage' : 'https://www.youtube.com/watch?v=3YIjiZiltPs&list=PLCR3KcbG-XGu1fSZ2N675NLUWj7w1GfNJ&index=1'}
             
    #scrape the playlists for the video titles
    video_titles = {}
    for tourney in playlists:
        video_titles[tourney] = yt_playlist_scraper(playlists[tourney])
        print("Done with tourney")
    
    #parse the video titles into a dictionary
    video_info = title_Parser(video_titles)

    #pass the dictionary to mongo
    video_db.videos.insert_many(video_info)
    

main()
