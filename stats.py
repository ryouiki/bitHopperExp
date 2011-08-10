#License#
#bitHopper by Colin Rice is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#Based on a work at github.com.

import diff
import pool
import work
import json
import database

def parse_mtred(response, bitHopper):
    info = json.loads(response)
    myshare = int(info['rsolved'])
    round_shares = int(info['server']['roundshares'])+1

    estimated = 50.0 * myshare/round_shares
    luck = bitHopper.difficulty.get_btc_difficulty()/round_shares
    
    serverInfo = bitHopper.pool.get_entry('mtred')
    database.update_stat('mtred', round_shares, bitHopper.difficulty.get_btc_difficulty(), myshare, serverInfo['accept'], serverInfo['reject'])
    bitHopper.log_msg('mtr est : {0:.6f} / {1:.2}x chance'.format(estimated, luck))

def parse_bitclockers(response, bitHopper):
    info = json.loads(response)
    actual = 0.0
    balances  = ['balance', 'estimatedearnings', 'payout']
    for item in balances:
        actual += float(info[item])

    shares = 0.0
    shares += info['totalshares']

    expected = shares/bitHopper.difficulty.get_btc_difficulty() * 50

    if expected != 0.0:
        bitHopper.log_msg('bitclockers efficiency: {0:.2%}%'.format(actual/expected))

def parse_bitp(response, bitHopper):
    info = json.loads(response)
    myshare = int(info['shares'])
    estimated = float(info['estimated_reward'])+0.0000001
    round_shares = int(myshare * 50 / estimated)
    luck = bitHopper.difficulty.get_btc_difficulty()/round_shares

def parse_nofee(response, bitHopper):
    info = json.loads(response)
    round_shares = int(info['poolRoundShares'])
    estimated = float(info['estimated_reward'])+0.0000001
    myshare = int( estimated * round_shares / 50.0 )
    luck = bitHopper.difficulty.get_btc_difficulty()/round_shares

    serverInfo = bitHopper.pool.get_entry('nofee')
    database.update_stat('nofee', round_shares, bitHopper.difficulty.get_btc_difficulty(), myshare, serverInfo['accept'], serverInfo['reject'])
    bitHopper.log_msg('nofee est : {0:.6f} / {1:.2}x chance'.format(estimated, luck))

def selectsharesResponse(response, args):
    bitHopper = args[1]
    func_map= {
        'bitclockers':parse_bitclockers,
        'mtred':parse_mtred,
        'nofee':parse_nofee,
        'bitp':parse_bitp}
    pool = args[0]
    func = globals()['parse_'+pool]
    if (func) : func(response,bitHopper)
    bitHopper.server_update()

def errsharesResponse(error, args): 
    bitHopper = args[1]
    bitHopper.log_msg('Error in user api for> ' + str(args)+str(error))
    bitHopper.log_dbg(str(error))

def update_api_stats(bitHopper):
    servers = bitHopper.pool.get_servers()
    for server in servers:
    	update = ['info','mine']
        if 'user_api_address' in servers[server] and servers[server]['role'] in update:
            info = servers[server]
            d = work.get(bitHopper.json_agent,info['user_api_address'])
            d.addCallback(selectsharesResponse, (server,bitHopper))
            d.addErrback(errsharesResponse, (server,bitHopper))
            d.addErrback(bitHopper.log_msg)

def stats_dump(server, stats_file, btc_diff, nmc_diff ):
    if stats_file != None:
        stats_file.write(pool.get_entry(pool.get_current())['name'] + " "
           + str(pool.get_entry(pool.get_current())['user_shares'])
           + " btc diff " + str(btc_diff)
           + " nmc diff " + str(nmc_diff) + "\n")
