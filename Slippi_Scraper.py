from splinter import Browser
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import time
import re
from slippi import Game

def slippi_scraper(tournament,filter,page='1'):
    #initialize the browser properly
    prefs = {
            "download.default_directory" : f"C:/Users/Cuno/Desktop/ETL proj/Replays"
        }
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("prefs", prefs)
    #this is an attempt to make the downloads succeed by 'spoofing' an agent-string
    agent_string = "Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19"
    #go to 'base' page for the passed tournament
    with Browser('chrome', 
                 headless=False, 
                 options=chrome_options, 
                 user_agent=agent_string) as browser:
        url = f"https://slippi.gg/tournament/{tournament}?filter={filter}&page={page}"
        browser.visit(url)
        time.sleep(1)

        
    #find all the download links, click all of them, then try to go to the next page
    #if the next page button is missing, say we're done
        while True:
            DL_links = browser.links.find_by_partial_href('storage')

            for i in range(len(DL_links)):
                DL_links[i].click()
                time.sleep(0)
                #print(DL_links[i])
            try:
                browser.find_by_css('svg').last.click()
            except:
                break
            #FOR DEBUG ONLY <can be removed later>
            finally:
                time.sleep(1)
                print(browser.url)

tourneyID_dict = {'Smash Summit 8' : 97437,
                'Shine 2019' : 98817,
                'Mainstage' : 101818,
                'The Big House 9' : 109637}
filter_dict = ['Day+3','Day+4',
               'BTSSmash','BTSSmash2','BTSSmash3','BTSSmash4',
               'BTSsmash','BTSsmash2','BTSsmash3','BTSsmash4']                

#for key in tourneyID_dict:
    #for filter in filter_dict:
        #slippi_scraper(tourneyID_dict[key],filter)
    
#test run, only has 2 download links on the page
slippi_scraper('109637','BTSSmash',page='19')