import riotwatcher as rw
from collections import defaultdict
from copy import deepcopy
import requests
import datetime
import time


class RiotAPI:
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.num_requests = 0
    
    def request(self, api_url):
        req = requests.get(f'{api_url}api_key={self.api_key}').json()
        
        while req == {'status': {'message': 'Rate limit exceeded', 'status_code': 429}}:
            time.sleep(1.01)
            req =  requests.get(f'{api_url}api_key={self.api_key}').json()
            if req == {'status': {'message': 'Rate limit exceeded', 'status_code': 429}}:
                #print("num requests:", self.num_requests)
                #print("Waiting, rate limit...")
                time.sleep(30.01)
            req = requests.get(f'{api_url}api_key={self.api_key}').json()
        
        while 'status' in req and req['status']['status_code'] != 200 and req['status']['status_code'] != 404:
            print('ERROR:', req)
            time.sleep(5.01)
            req =  requests.get(f'{api_url}api_key={self.api_key}').json()
            
        self.num_requests += 1
        return req
    
    def get_seed(self, date):
        entries = self.request(f'https://na1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/DIAMOND/IV?page=1&')
        #print(entries)
        
        for i in entries:
            #print(self.request(f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/{i['summonerId']}?"))
            puuid = self.request(f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/{i['summonerId']}?")['puuid']
            
            matches = self.request(f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?startTime={date}&endTime={date+86400}&queue=420&type=ranked&start=0&count=20&")
            if matches != []:
                return matches, puuid
            
    def spam_requests(self):
        for i in range(500):
            print(i)
            self.request(f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/'-c0wItVzJL-iQMRhPoYqNCDsqf039te1kIBMxw3FWVyfslAFhcwvgdocBGgXwicPGGHtiqZkTIsC0w'/ids?startTime=1649314800&endTime={1649314800+86400}&queue=420&type=ranked&start=0&count=20&")
        
    def crawl(self, date, count):
        matches, seed = self.get_seed(date)
        searched_ids = set(seed)
        searched_matches = set()
        champ_info = defaultdict(int)
        champ_info['count'] = 0
        frontier = matches

        while champ_info['count'] < count:

            
            new_frontier = []
            for match_id in frontier:
                    if champ_info['count'] % 20 == 0:
                        print('Match number: ', champ_info['count'])
                    searched_matches.add(match_id)
                    match = self.request(f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}?")
                    found = False
                    if 'status' in match and match['status']['status_code'] == 404:
                        return champ_info
                    
                    for p in match['info']['participants']:
                        
                        champ_info[p['championName']] += 1

                        if p['puuid'] not in searched_ids and not found:
                            searched_ids.add(p['puuid'])
                            new_matches = self.request(f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{p['puuid']}/ids?startTime={date}&endTime={date+86400}&queue=420&type=ranked&start=0&count=20&")
                            for new_id in new_matches:
                                if new_id not in searched_matches:
                                    new_frontier.append(new_id)
                                    found = True

                    champ_info['count'] += 1
                    if champ_info['count'] > count:
                        return champ_info

            if new_frontier == []:
                return champ_info
            else:
                frontier = deepcopy(new_frontier)

        return champ_info


    