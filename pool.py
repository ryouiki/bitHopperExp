#License#
#bitHopper by Colin Rice is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#Based on a work at github.com.

import work
import json
import re
import time
import calendar
import database

from password import *

class Pool():
    def __init__(self, bitHopper):
        self.bitHopper = bitHopper
        
        default_shares = 10**10

        btc_difficulty = self.bitHopper.difficulty.get_btc_difficulty()
        nmc_difficulty = self.bitHopper.difficulty.get_nmc_difficulty()

        self.servers = {
                'deepbit':{ 'name':'deepbit.net', 
                    'mine_address':'pit.deepbit.net:8332', 'user':deepbit_user, 'pass':deepbit_pass, 
                    'api_address':'http://deepbit.net/api/' + deepbit_apikey, 'penalty':3 },
                'bitparking':{'shares':nmc_difficulty*.431, 'name':'BitParking',   # namecoin pool
                    'mine_address':'bitparking.com:9098', 'user':nmc_user, 'pass':nmc_pass,
                    'api_address':'http://bitparking.com/pool',
                    'cointype':'nmc', 'role':'disable', 'penalty':2},
                'namebit':{'shares':nmc_difficulty, 'name':'NameBit',   # namecoin pool
                    'mine_address':'pool.namebit.org:10000', 'user':namebit_user, 'pass':namebit_pass,
                    'api_address':'http://namebit.org/',
                    'cointype':'nmc', 'role':'disable', 'penalty':2},
                'bclc':{ 'name':'bitcoins.lc', 
                    'mine_address':'bitcoins.lc:8080', 'user':bclc_user, 'pass':bclc_pass, 
                    'api_address':'https://www.bitcoins.lc/stats.json', 'penalty':1.05 },
                'polmine':{ 'name':'polmine.pl', 
                    'mine_address':'polmine.pl:8347', 'user':polmine_user, 'pass':polmine_pass,
                    'api_address':'https://polmine.pl/?action=statistics' },
                'triple':{ 'name':'triplemining.com', 
                    'mine_address':'eu.triplemining.com:8344', 'user':triple_user, 'pass':triple_pass, 
                    'api_address':'http://api.triplemining.com/json/stats' },
                'nofee':{ 'name': 'nofee',
                    'mine_address': 'nofeemining.com:8332', 'user': nofee_user,
                    'pass': nofee_pass, 
                    'api_address':'http://www.nofeemining.com/api.php?key=' + nofee_user_apikey,
                    'user_api_address':'http://www.nofeemining.com/api.php?key=' + nofee_user_apikey },
                'mtred':{ 'name':'mtred',  
                    'mine_address':'mtred.com:8837', 'user':mtred_user, 'pass':mtred_pass,
                    'api_address':'https://mtred.com/api/user/key/' + mtred_user_apikey, 
                    'user_api_address':'https://mtred.com/api/user/key/' + mtred_user_apikey, 'wait':0.02, 'penalty':1.02 },
                'ozco':{ 'name': 'ozco.in',
                   'mine_address': 'ozco.in:8332', 'user': ozco_user, 'pass': ozco_pass,
                   'api_address':'https://ozco.in/api.php' },
                'rfc':{ 'name': 'rfcpool.com',
                    'mine_address': 'pool.rfcpool.com:8332', 'user': rfc_user, 'pass': 'x',
                    'api_address':'https://www.rfcpool.com/api/pool/stats' },
                'btcmonkey':{ 'name': 'bitcoinmonkey.com',
                    'mine_address': 'bitcoinmonkey.com:8332', 'user': btcmonkey_user, 'pass': btcmonkey_pass,
                    'api_address':'https://bitcoinmonkey.com/json/api.php' },
                'btcserv':{ 'name': 'btcserv.net',
                    'mine_address': 'btcserv.net:8335', 'user': btcserv_user, 'pass': btcserv_pass,
                    'api_address':'http://btcserv.net/' },
                'btcg':{ 'name':'BTC Guild',  
                    'mine_address':'us.btcguild.com:8332', 'user':btcguild_user, 'pass':btcguild_pass, 'penalty':4,
                    'api_address':'https://www.btcguild.com/'},
                'pool24':{ 'name': 'btcpool24.com', 
                    'mine_address': 'min.btcpool24.com:8338', 'user': pool24_user, 'pass': pool24_pass,
                    'api_address':'http://www.btcpool24.com/json_stats.php'},
                'bcpool':{ 'name': 'bitcoinpool.com', 
                    'mine_address': 'bitcoinpool.com:8334', 'user': bcpool_user, 'pass': bcpool_pass,
                    'api_address':'http://www.bitcoinpool.com/pooljson.php'},
                'bithasher':{ 'name': 'bithasher.com', 
                    'mine_address': 'bithasher.com:8332', 'user': bithasher_user, 'pass': bithasher_pass,
                    'api_address':'http://bithasher.com'},
                'swepool':{ 'name': 'swepool.net', 
                    'mine_address': 'swepool.net:8337', 'user': swepool_user, 'pass': swepool_pass,
                    'api_address':'http://swepool.net/json?key=' + swepool_user_apikey   },
                'btcmp':{ 'name': 'btcmp.com', 
                    'mine_address': 'rr.btcmp.com:8332', 'user': btcmp_user, 'pass': btcmp_pass,
                    'api_address':'http://www.btcmp.com/methods/pool/pool_get_stats' },
                
                'bitclockers':{ 'name': 'bitclockers.com',  # not stable
                    'mine_address': 'pool.bitclockers.com:8332', 'user': bitclockers_user, 'pass': bitclockers_pass,
                    'api_address':'https://bitclockers.com/api',
                    'user_api_address':'https://bitclockers.com/api/'+bitclockers_user_apikey, 'role':'disable' },
                'bmunion':{ 'name': 'bitminersunion',       # not stable 
                    'mine_address': 'pool.bitminersunion.org:8341', 'user': bmu_user, 'pass': bmu_pass,
                    'api_address':'http://67.249.146.78/stats.php', 'role':'disable'},
                'digbtc':{ 'name': 'http://digbtc.net/',    # not stable
                    'mine_address': '96.126.111.65:8332', 'user': digbtc_user, 'pass': digbtc_pass,
                    'api_address':'http://digbtc.net/', 'role':'disable'},
                'eligius':{'shares':btc_difficulty*.431, 'name':'eligius',       # SMPPS, backup pool
                    'mine_address':'su.mining.eligius.st:8337', 'user':eligius_address, 'pass':'x', 'penalty':3,
                    'paytype':'smpps', 'role':'backup'},
                'arsbitcoin':{'shares':btc_difficulty*.431, 'name':'arsbitcoin', #SMPPS, backup pool
                    'mine_address':'arsbitcoin.com:8344', 'user':ars_user, 'pass':ars_pass, 'penalty':2,
                    'paytype':'smpps', 'role':'backup'},
                'bitp':{ 'name': 'bitp.it',                                      # SMPPS, backup pool
                    'mine_address': 'pool.bitp.it:8334', 'user': bitp_user, 'pass': bitp_pass,
                    'api_address':'https://pool.bitp.it/leaderboard',
                    'user_api_address':'https://pool.bitp.it/api/user?token=' + bitp_user_apikey,
                    'paytype':'smpps', 'role':'backup'},
                        
                # hopping PPLNS or scoring(slush) pools are not recommended
                # in simulations,
                # with existing 9 proportional pools, adding one PPLNS or scoring pool enhances only 0 ~ 2% total efficiency at best
                # classic < 0.1 mining also harms 1% total eff (normal hopping would harm 4% damage) 
                # while adding one more proportional pool enhances ~7% total eff gain
                # try at your own risk ;)
                
                'slush':{ 'name':'bitcoin.cz',   # scoring 
                    'mine_address':'api2.bitcoin.cz:8332', 'user':slush_user, 'pass':slush_pass, 
                    'api_address':'http://mining.bitcoin.cz/stats/json/', 'paytype':'score', 'role':'disable' },
                'mineco':{ 'name': 'mineco.in',  # PPLNS
                    'mine_address': 'mineco.in:3000', 'user': mineco_user, 'pass': mineco_pass,
                    'api_address':'https://mineco.in/stats.json', 'paytype':'pplns', 'role':'disable' },
                        
                'unitedminers':{ 'name': 'unitedminers.com', # PPLNS
                    'mine_address': 'pool.unitedminers.com:8332', 'user': unitedminers_user, 'pass': unitedminers_pass,
                    'api_address':'http://www.unitedminers.com/?action=api', 'paytype':'pplns', 'role':'removefromlist' },
                'eclipsemc':{ 'name': 'eclipsemc.com', # scoring system not test yet
                    'mine_address': 'pacrim.eclipsemc.com:8337', 'user': eclipsemc_user, 'pass': eclipsemc_pass, 'paytype':'score', 'role':'removefromlist',
                    'api_address':'https://eclipsemc.com/api.php?key='+ eclipsemc_apikey +'&action=poolstats' },
                'miningmainframe':{ 'name': 'mining.mainframe.nl', # scoring system not test yet
                    'mine_address': 'mining.mainframe.nl:8343', 'user': miningmainframe_user, 'pass': miningmainframe_pass,
                    'api_address':'http://mining.mainframe.nl/api', 'paytype':'score', 'role':'removefromlist'},                
                'itzod':{ 'name': 'http://pool.itzod.ru', # scoring system not test yet
                    'mine_address': 'lp1.itzod.ru:8344', 'user': itzod_user, 'pass': itzod_pass,
                    'api_address':'http://pool.itzod.ru/api.php', 'paytype':'score', 'role':'removefromlist'},
                'poolmunity':{ 'name':'poolmunity.com',   # scoring system not test yet
                    'mine_address':'poolmunity.com:8332', 'user':poolmunity_user, 'pass':poolmunity_pass, 
                    'api_address':'https://poolmunity.com/api.php?server', 'role':'removefromlist' },
                'x8s':{ 'name': 'btc.x8s.de', # closed
                    'mine_address': 'pit.x8s.de:8337', 'user': x8s_user, 'pass': x8s_pass,
                    'api_address':'http://btc.x8s.de/api/global.json', 'paytype':'pplns', 'role':'removefromlist'},
                }

        serverTemplate = { 'shares': default_shares, 
            'wait':0.0, 'penalty':1.0, 'lag':False, 'LP':None, 'accept':0, 'reject':0, 'forced':0,
            'role':'mine', 'paytype':'prop', 'cointype':'btc', 'my_round_share':0, 'duration':0, 'isDurationEstimated':True, 'duration_temporal':0, 'duration_share':0, 'ghash':0 }

        for server in self.servers:
            for k in serverTemplate:
                if k not in self.servers[server]:
                   self.servers[server][k] = serverTemplate[k]

        self.current_server = ''

        for server in self.servers.keys():
            if self.servers[server]['role'] == 'removefromlist':
                del self.servers[server]
                continue
            elif self.servers[server]['role'] == 'backup':
                self.current_server = server
            if self.servers[server]['paytype'] == 'pplns':    # not analytically proven. but chosen near-optimal value from simulations
                if self.servers[server]['wait'] == 0:         # this configuration would be safer than conventional <0.1 mining
                    self.servers[server]['wait'] = 0.33
                    self.servers[server]['penalty'] = 1.5
            elif self.servers[server]['paytype'] == 'score':  # not analytically proven. but chosen near-optimal value from simulations
                if self.servers[server]['wait'] == 0:         # this configuration would be safer than conventional <0.1 mining
                    self.servers[server]['wait'] = 0.32
                    self.servers[server]['penalty'] = 1.2

        self.updateInterval = 57

    def get_entry(self, server):
        if server in self.servers:
            return self.servers[server]
        else:
            return None

    def get_servers(self, ):
        return self.servers

    def get_current(self, ):
        return self.current_server

    def set_current(self, server):
        self.current_server = server

    def Force(self, poolName, duration = 300, forceSet = False):
        forced = False
        for server in self.servers:
            if server == poolName and self.servers[server]['role']!='disable':
                forced = True
                if forceSet==True:
                    self.servers[server]['forced'] = duration
                else:
                    self.servers[server]['forced'] += duration
            else:
                self.servers[server]['forced'] = 0
        
        if forced==True:
            self.bitHopper.select_best_server()

    def UpdateShares(self, server, shares, duration_forced = False):
        info = self.servers[server]
        if duration_forced == True:
            info['isDurationEstimated'] = False
            if info['duration'] * info['ghash'] * 0.25 * 0.2 > shares:
                # checks fake / suspicious small share (poolmunity does it)
                self.bitHopper.log_msg( 'Fake Share > {0} : {1} | {2} min : {3} GH'.format(server, shares, int(info['duration'])/60, float(info['ghash']) ) )
                shares = 10**10
        try:
            k =  str('{0:,d}'.format(shares))
        except Exception, e:
            k =  str(shares)
        
        info['duration_temporal'] += self.updateInterval
        if info['duration'] > 0:
            info['duration'] += self.updateInterval
        if info['shares'] != shares:
            if 0.5 * info['shares'] > shares:   # guess next round has come..
                info['my_round_share'] = 0
                if info['ghash'] > 0:
                    # speed already known
                    sharePerSec = info['ghash'] / 4.0
                    info['duration_temporal'] = self.updateInterval
                    info['duration_share'] = sharePerSec * info['duration_temporal']
                    if duration_forced == False:
                        info['duration'] = shares / sharePerSec + 1
                        if info['shares'] == 10**10:  # in case of re-enabled pool
                            info['isDurationEstimated'] = True
                        else:
                            info['isDurationEstimated'] = False
                else:
                    # speed not known (not estimated yet) sorry for the magic numbers
                    info['duration_temporal'] = 10
                    info['duration_share'] = 10
                    info['ghash'] = 40
                    # 
                    info['duration'] = shares / (info['ghash']/4)
                    info['isDurationEstimated'] = True
            elif info['shares'] < shares:
                info['duration_share'] = info['duration_share'] + (shares - info['shares'])
                sharePerSec = float(info['duration_share']) / info['duration_temporal']
                oldSpeed = info['ghash'] + 0.01
                info['ghash'] =  sharePerSec * 4.0 + 0.01
                if info['duration_temporal'] > 300 and info['isDurationEstimated'] == True:
                    # re-estimate round duration (every 5 minutes)
                    info['duration'] = int(info['shares'] / (info['ghash']/4) )
                if info['duration_temporal'] > 600:
                    # retune to adapt trend (after first 10 minutes, every 6.66 minutes)
                    info['duration_temporal'] = 200
                    info['duration_share'] = int( sharePerSec * 200 )
                    if info['isDurationEstimated'] == True and float(abs(oldSpeed - info['ghash']))/oldSpeed < 0.05:
                        # if estimated speed stabilized (speed delta is within 5%), don't estimate round duration later
                        info['isDurationEstimated'] = False

            info['shares'] = shares
            total = info['accept'] + info['reject']
            difficulty = self.bitHopper.difficulty.get_btc_difficulty()
            if info['cointype'] == 'nmc':
                difficulty = self.bitHopper.difficulty.get_nmc_difficulty()

            if total > 0:
                database.update_stat(server, shares, difficulty, -1, info['accept'], info['reject'])
                self.bitHopper.log_msg( 'Share > {0} : {1} ({2}) | rejection rate {3}/{4} = {5:.2%} | {6} min'.format(server, k, info['my_round_share'], info['reject'], total, float(info['reject'])/total, int(info['duration']/60) ) )
            else:
                database.update_stat(server, shares, difficulty, -1, info['accept'], info['reject'])
                self.bitHopper.log_msg( 'Share > {0} : {1} | {2} min'.format(server, k, int(info['duration']/60)) )

    def deepbit_sharesResponse(self, response):
        round_shares = self.bitHopper.difficulty.get_btc_difficulty()*0.431
        self.UpdateShares('deepbit',round_shares)

    def slush_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['shares'])
        server = self.servers['slush']
        server['ghash'] = float(info['ghashes_ps'])
        server['duration'] = 0
        durationStrings = info['round_duration'].split(':')
        for i in durationStrings:
            server['duration'] = server['duration'] * 60 + int(i)
        self.UpdateShares('slush',round_shares, True)

    def ozco_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['shares'])
        server = self.servers['ozco']
        server['ghash'] = float(info['hashrate']) / 1000
        server['duration'] = int(info['roundduration'])
        self.UpdateShares('ozco',round_shares, True)

    def nofee_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['poolRoundShares'])
        server = self.servers['nofee']
        server['ghash'] = float(info['poolspeed'])
        self.UpdateShares('nofee',round_shares)

    def mmf_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['shares_this_round'])
        self.UpdateShares('miningmainframe',round_shares)

    def bitp_sharesResponse(self, response):
        outputs = re.finditer('<tr>\s+<td>\d+</td>\s+<td>.+\s+<td>(\d+)', response)
        round_shares = 0
        for output in outputs:
            round_shares += int(output.group(1))
        self.UpdateShares('bitp',round_shares)

    def eclipsemc_sharesResponse(self, response):
        info = json.loads(response[:response.find('}')+1])
        round_shares = int(info['round_shares'])
        self.UpdateShares('eclipsemc',round_shares)

    def btcg_sharesResponse(self, response):
        round_shares = self.bitHopper.difficulty.get_btc_difficulty()*0.431
        self.UpdateShares('btcg',round_shares)

    def bclc_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['round_shares'])
        server = self.servers['bclc']
        server['ghash'] = float(long(info['hash_rate'])/1000000)/1000
        server['duration'] = int(time.time() - int(info['round_started']))
        self.UpdateShares('bclc',round_shares, True)
   
    def polmine_sharesResponse(self, response):
        #output = re.search(r"stkich: &nbsp; </b> <br/>([ 0-9]+)<br/>", response)
        output_duration = re.search(r"&nbsp; </b> <br/> (\d+) dni (\d+) godzin (\d+) minut (\d+) sekund", response)
        output_speed = re.search(r"kopalni to<b>([ 0-9\.]+)</b>", response)
        if output_speed != None and output_duration != None:
            duration = int(output_duration.group(1)) * 24 * 3600 + int(output_duration.group(2)) * 3600 + int(output_duration.group(3)) * 60 + int(output_duration.group(4))
            speed = float(output_speed.group(1))
            server = self.servers['polmine']
            round_shares = speed * duration * 0.25
            server['ghash'] = speed
            server['duration'] = duration
            self.UpdateShares('polmine',round_shares, True)
        else:
            self.bitHopper.log_msg('regex fail : polmine')

    def rfc_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['poolstats']['round_shares'])
        server = self.servers['rfc']
        server['ghash'] = float(info['poolstats']['hashrate'])
        server['duration'] = int(info['poolstats']['round_time'])
        self.UpdateShares('rfc',round_shares, True)
    
    def x8s_sharesResponse(self, response):
        round_shares = int(json.loads(response)['round_shares'])
        self.UpdateShares('x8s',round_shares)
    
    def namebit_sharesResponse(self, response):
        output = re.search("current_share_count\">(\d+)</td>", response)
        round_shares=0
        if output != None:
            round_shares = int(output.group(1))
            self.UpdateShares('namebit',round_shares)
    
    def bitparking_sharesResponse(self, response):
        output = re.search("Shares in current block</td><td>(\d+)</td>", response)
        round_shares=0
        if output != None:
            round_shares = int(output.group(1))
            self.UpdateShares('bitparking',round_shares)

    def triple_sharesResponse(self, response):
        #parsed = response.replace('\n', '').replace('\r','').replace('\t','').replace(' ','')
        #output = re.search('-->(\d+)</td><td>-</td>', parsed)
        #if output != None:
        #    round_shares = int(output.group(1))
        #    self.UpdateShares('triple',round_shares)
        #else:
        #    self.bitHopper.log_msg('regex fail : triple')
        round_shares = int(json.loads(response)['solved'])
        self.UpdateShares('triple',round_shares)

    def poolmunity_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int( info['totalShares'])
        server = self.servers['poolmunity']
        server['ghash'] = float(info['speed']) / 1000.0
        server['duration'] = int(time.time() - int(info['roundStarted']))
        self.UpdateShares('poolmunity',round_shares, True)

    def mtred_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['server']['roundshares'])
        server = self.servers['mtred']
        server['ghash'] = float(info['server']['hashrate'])
        self.UpdateShares('mtred',round_shares)

    def swepool_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['round_shares'])
        server = self.servers['swepool']
        server['ghash'] = float(info['pool_speed'])/1000000000.0
        server['duration'] = int(info['round_time'])
        self.UpdateShares('swepool',round_shares, True)

    def mineco_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['shares_this_round'])
        server = self.servers['mineco']
        server['ghash'] = float(info['hashrate']) / 10**9
        self.UpdateShares('mineco',round_shares)
        
    def btcmonkey_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['shares_this_round'])
        speed = int(info['pool_total_mhash'])/1000.0
        server = self.servers['btcmonkey']
        server['ghash'] = speed
        self.UpdateShares('btcmonkey',round_shares)
        
        
    def unitedminers_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['validcurrentshares'])
        speed = float(info['hashrate'])/1000.0
        server = self.servers['unitedminers']
        server['ghash'] = speed
        self.UpdateShares('unitedminers',round_shares)

    def btcserv_sharesResponse(self, response):
        spaceRemoved = response.replace('\n', '').replace('\r','').replace('\t','').replace(' ','').replace(',','')
        shareMatch = re.search('span>(\d+)shares<span', spaceRemoved)
        speedMatch = re.search('span>([\.0-9]+)GHash/s<span', spaceRemoved)
        isGhash = True
        if speedMatch == None:
            speedMatch = re.search('span>([\.0-9]+)MHash/s<span', spaceRemoved)
            isGhash = False
        if shareMatch != None and speedMatch != None:
            round_shares = int(shareMatch.group(1))
            speed = float(speedMatch.group(1))
            server = self.servers['btcserv']
            if isGhash == True:
                server['ghash'] = speed
            else:
                server['ghash'] = speed * 0.001
            self.UpdateShares('btcserv',round_shares)
        else:
            self.bitHopper.log_msg('regex fail : btcserv')

    def bmunion_sharesResponse(self, response):
        output = re.search("this round:([ 0-9]+)<br/>", response)
        if output != None:
            round_shares = int(output.group(1))
            server = self.servers['bmunion']
            self.UpdateShares('bmunion',round_shares)
        else:
            self.bitHopper.log_msg('regex fail : bmunion')
            
    def bitclockers_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['roundshares'])
        server = self.servers['bitclockers']
        server['ghash'] = float(info['hashrate']) / 1000.0
        self.UpdateShares('bitclockers',round_shares)

    def pool24_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['shares_this_round'])
        server = self.servers['pool24']
        server['ghash'] = float(info['hashrate']) / 1000.0
        server['duration'] = int(info['round_duration_sec'])
        self.UpdateShares('pool24',round_shares, True)
        
    def bcpool_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['round_shares'])
        server = self.servers['bcpool']
        server['ghash'] = float(info['hashrate'])
        durationStrings = info['round_duration'].split(':')
        server['duration'] = int(durationStrings[0]) * 24 * 60 * 60 + int(durationStrings[1]) * 60 * 60 + int(durationStrings[2]) * 60 + int(durationStrings[3])
        self.UpdateShares('bcpool',round_shares, True)
        
    def itzod_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['total_shares_count'])
        server = self.servers['itzod']
        server['ghash'] = float(info['total_speed'])/1000.0
        server['duration'] = int(info['calc_time'])
        self.UpdateShares('itzod',round_shares, True)
        
    def bithasher_sharesResponse(self, response):
        shareMatch = re.search('Round Shares</td><td>([,0-9]+)<', response)
        speedMatch = re.search('Hash Rate</td><td>([.0-9]+) gh', response)
        durationMatch = re.search('Round Time</td><td>([:0-9]+)<', response)
        if shareMatch != None and speedMatch != None and durationMatch != None:
            round_shares = int(shareMatch.group(1).replace(',',''))
            server = self.servers['bithasher']
            durationStrings = durationMatch.group(1).split(':')
            server['duration'] = int(durationStrings[0]) * 60 * 60 + int(durationStrings[1]) * 60 + int(durationStrings[2])
            server['ghash'] = float(speedMatch.group(1))
            self.UpdateShares('bithasher',round_shares, True)
        else:
            self.bitHopper.log_msg('regex fail : bithasher')

    def digbtc_sharesResponse(self, response):
        shareMatch = re.search('Round Shares</td><td>([,0-9]+)<', response)
        match = re.search('Hash: <b>([\.0-9]+)GH/s</b> Round Shares: <b>(\d+)</b> Round Time: <b>([:0-9]+)</b>', response)
        if match != None:
            round_shares = int(match.group(2))
            server = self.servers['digbtc']
            durationStrings = match.group(3).split(':')
            server['duration'] = int(durationStrings[0]) * 60 * 60 + int(durationStrings[1]) * 60 + int(durationStrings[2])
            server['ghash'] = float(match.group(1))
            self.UpdateShares('digbtc',round_shares, True)
        else:
            self.bitHopper.log_msg('regex fail : digbtc')

    def btcmp_sharesResponse(self, response):
        info = json.loads(response)
        round_shares = int(info['round_shares'])
        server = self.servers['btcmp']
        server['ghash'] = float(info['shares_per_second'])*4
        time_string = info['round_start'].split('.')[0]
        server['duration'] = time.time() - calendar.timegm(time.strptime(time_string, "%Y-%m-%dT%H:%M:%S")) + 7200
        self.UpdateShares('btcmp',round_shares, True)

    def errsharesResponse(self, error, args):
        self.bitHopper.log_msg('Error in pool api for ' + str(args) + str(error))
        self.bitHopper.log_dbg(str(error))
        pool = args
        if self.servers[pool]['role'] != 'disable':
            self.servers[pool]['lag'] = True
        self.servers[pool]['shares'] = 10**10

    def selectsharesResponse(self, response, args):
        self.bitHopper.log_dbg('Calling sharesResponse for '+ args)
        func = getattr(self, args + '_sharesResponse', None)
        if func != None:
            func(response)
        self.bitHopper.server_update()

    def update_api_servers(self):
        for server in self.servers:
            info = self.servers[server]
            update = ['info','mine']
            if server=='btcmp':
                d = work.get_btcmp(self.bitHopper.json_agent,info['api_address'])
                d.addCallback(self.selectsharesResponse, (server))
                d.addErrback(self.errsharesResponse, (server))
                d.addErrback(self.bitHopper.log_msg)
            elif info['role'] in update:
                d = work.get(self.bitHopper.json_agent,info['api_address'])
                d.addCallback(self.selectsharesResponse, (server))
                d.addErrback(self.errsharesResponse, (server))
                d.addErrback(self.bitHopper.log_msg)
            elif info['role'] == 'backup':
                total = info['accept'] + info['reject']
                if total > 0:
                    self.bitHopper.log_msg( 'Backup {0} > {1}/{2} = {3:.2%}'.format(info['name'], info['accept'], total, float(info['accept'])/total ) )

if __name__ == "__main__":
    print 'Run python bitHopper.py instead.'
