#!/bin/env python
#License#
#bitHopper by Colin Rice is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#Based on a work at github.com.

import json
import work
import diff
import pool
import os
import getwork_store
import blockinfo

import database
import sys
import exceptions
import optparse
import time
import lp

from twisted.web import server, resource
from client import Agent
from _newclient import Request
from twisted.internet import reactor, defer
from twisted.internet.defer import Deferred
from twisted.internet.task import LoopingCall
from twisted.python import log, failure

class BitHopper():
    def __init__(self):
        self.json_agent = Agent(reactor)
        self.lp_agent = Agent(reactor, persistent=True)
        self.new_server = Deferred()
        self.options = None
        
        self.difficulty = diff.Difficulty(self)
        LoopingCall(self.difficulty.update_difficulty).start(60*60*3)
        
        self.pool = pool.Pool(self)
        self.lp = lp.LongPoll(self)
        self.shareCounter = 0
        self.mHashes = 0
        self.getwork_store = getwork_store.Getwork_store()
        
        blockinfo.BlockInfo(self)
    
    def tick(self):
        #called every three second
        for server in self.pool.get_servers():
            info = self.pool.get_entry(server)
            if info['forced'] > 0:
                info['forced'] -= 3
                if info['forced'] <= 0:
                    info['forced'] = 0
                    self.select_best_server()
                break   # there must be only one forced server
    
    def recentInfo(self):
        self.mHashes = int((self.mHashes + (float(self.shareCounter) * (2**32)) / (120 * 1000000))* 0.5 )
        self.shareCounter = 0

    def lp_callback(self, ):
        reactor.callLater(0.1,self.new_server.callback,None)
        self.new_server = Deferred()

    def get_json_agent(self, ):
        return self.json_agent

    def get_lp_agent(self, ):
        return self.lp_agent

    def get_options(self, ):
        return self.options

    def log_msg(self, msg):
        if self.get_options() == None:
            print time.strftime("[%H:%M:%S] ") +str(msg)
            return
        if self.get_options().debug == True:
            log.msg(msg)
            return
        print time.strftime("[%H:%M:%S] ") +str(msg)

    def log_dbg(self, msg):
        if self.get_options() == None:
            log.err(msg)
            return
        if self.get_options().debug == True:
            log.err(msg)
            return
        return

    def get_server(self, ):
        return self.pool.get_current()

    def get_progress(self, server):
        type_diff = { 'btc':self.difficulty.get_btc_difficulty(), 'nmc':self.difficulty.get_nmc_difficulty() }
        info = self.pool.get_entry(server)
        return info['shares'] * info['penalty'] / type_diff[info['cointype']]

    def select_best_server(self, ):
        """selects the best server for pool hopping. If there is not good server it returns SMPPS pool"""
        server_name = None

        threshold = 0.43
        min_progress = threshold

        for server in self.pool.get_servers():
            info = self.pool.get_entry(server)
            if info['forced'] > 0:
                server_name = server
                break

        # back to minimum round share based selection, until convinced to new algorithms
        
        if server_name == None:
            for server in self.pool.get_servers():
                info = self.pool.get_entry(server)
                if info['role'] != 'mine' or info['lag'] == True or info['paytype'] != 'prop':
                    continue
                share_progress = self.get_progress(server)
                if share_progress < min_progress:
                    min_progress = share_progress
                    server_name = server
        
        # for score / pplns pools
        # they should always be checked after prop. pools because their efficiency is always lower than prop. pools
        # mining only 1/3 of default threshold(0.43 / 3 ) for prop. pools
        if server_name == None:
            min_progress = threshold * 0.25
            for server in self.pool.get_servers():
                info = self.pool.get_entry(server)
                if info['role'] == 'disable' or info['lag'] == True:
                    continue
                if info['paytype'] != 'score' and info['paytype'] != 'pplns':
                    continue
                share_progress = self.get_progress(server)
                if share_progress < min_progress:
                    min_progress = share_progress
                    server_name = server
        
        if server_name == None:
            # oops, there is no proper server
            # look for 'role':'backup' (SMPPS) pools with no lag
            min_reject = 10**10
            for server in self.pool.get_servers():
                info = self.pool.get_entry(server)
                if info['role'] != 'backup' or info['lag'] == True:
                    continue
                if min_reject > (info['reject'] * info['penalty']) :
                    min_reject = (info['reject'] * info['penalty'])
                    server_name = server

        if server_name == None:
            # OMG there's no good backup server..
            # we must look for sub-optimal(minimal share progress) pool with no lag
            min_progress = threshold
            for server in self.pool.get_servers():
                info = self.pool.get_entry(server)
                if info['role'] != 'mine' or info['paytype'] != 'prop':
                    continue
                share_progress = self.get_progress(server)
                if share_progress < min_progress:
                    min_progress = share_progress
                    server_name = server

        if server_name == None:
            # OMG OMG it is hopeless..
            # just select a bad (not worst) among backup pool
            min_reject = 10**10
            for server in self.pool.get_servers():
                info = self.pool.get_entry(server)
                if info['role'] != 'backup':
                    continue
                if min_reject > (info['reject'] * info['penalty']):
                    min_reject = (info['reject'] * info['penalty'])
                    server_name = server

        if self.pool.get_current() != server_name:
            self.pool.set_current(server_name)
            self.log_msg("Server change to " + str(self.pool.get_current()) + ", telling client with LP")
            self.lp_callback()      
            self.lp.clear_lp()
            
        return

    def get_new_server(self, server):
        currentServer = self.pool.get_entry(self.pool.get_current())
        if server != currentServer:
            return currentServer
        currentServer['lag'] = True
        self.select_best_server()
        return currentServer

    def server_update(self, ):
        self.select_best_server()

    @defer.inlineCallbacks
    def delag_server(self):
        self.log_dbg('Running Delager')
        for index in self.pool.get_servers():
            server = self.pool.get_entry(index)
            if server['role'] != 'disable' and server['lag'] == True:
                data = yield work.jsonrpc_call(self.json_agent, server,[], None)
                if data != None:
                    server['lag'] = False

bithopper_global = BitHopper()

def bitHopper_Post(request):
    content = request.content.read()
    if not bithopper_global.options.noLP:
        request.setHeader('X-Long-Polling', '/LP')
    rpc_request = json.loads(content)
    #check if they are sending a valid message
    if rpc_request['method'] != "getwork":
        return json.dumps({'result':None, 'error':'Not supported', 'id':rpc_request['id']})

    #Check for data to be validated
    currentServer = bithopper_global.pool.get_current()
    
    data = rpc_request['params']
    j_id = rpc_request['id']
    if data != []:
        storedServer = bithopper_global.getwork_store.get_server(data[0][72:136])
        if storedServer != None:
            currentServer = storedServer
        bithopper_global.shareCounter = bithopper_global.shareCounter + 1
    
    if bithopper_global.options.debug:
        bithopper_global.log_msg('RPC request ' + str(data) + " submitted to " + str(bithopper_global.pool.get_entry(currentServer)['name']))
    elif data != []:
        bithopper_global.log_msg('RPC request [' + str(data[0][152:160]) + "] submitted to " + str(bithopper_global.pool.get_entry(currentServer)['name']))

    work.jsonrpc_getwork(bithopper_global, currentServer, data, j_id, request)

    return server.NOT_DONE_YET

def bitHopperLP(value, *methodArgs):
    try:
        bithopper_global.log_msg('LP triggered serving miner')
        request = methodArgs[0]
        #Duplicated from above because its a little less of a hack
        #But apparently people expect well formed json-rpc back but won't actually make the call 
        try:
            json_request = request.content.read()
        except Exception,e:
            bithopper_global.log_dbg( 'reading request content failed')
            json_request = None
        try:
            rpc_request = json.loads(json_request)
        except Exception, e:
            bithopper_global.log_dbg('Loading the request failed')
            rpc_request = {'params':[],'id':1}
        #Check for data to be validated
        
        data = rpc_request['params']
        j_id = rpc_request['id']

        if request._disconnected == True:
            bithopper_global.log_msg('Client LP already disconnected')
        else:
            work.jsonrpc_getwork(bithopper_global, bithopper_global.pool.get_current(), data, j_id, request)

    except Exception, e:
        bithopper_global.log_msg('Error Caught in bitHopperLP')
        bithopper_global.log_dbg(str(e))
        try:
            request.finish()
        except Exception, e:
            bithopper_global.log_dbg( "Client already disconnected Urgh.")

    return None

class lpSite(resource.Resource):
    isLeaf = True
    def render_GET(self, request):
        bithopper_global.new_server.addCallback(bitHopperLP, (request))
        return server.NOT_DONE_YET

    def render_POST(self, request):
        bithopper_global.new_server.addCallback(bitHopperLP, (request))
        return server.NOT_DONE_YET

    def getChild(self,name,request):
        return self

class bitSite(resource.Resource):
    isLeaf = True
    
    def __init__(self):
        self.htmlString = '<html>void</html>'
        htmlFile = 'index.html'
        try:
            __file__
        except NameError:
            pass
        else:
            htmlFile=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html' )

        file = open(htmlFile, 'r')
        self.htmlString = file.read()
        file.close
    
    def render_GET(self, request):
        strReq = str(request)
        
        # do commands
        if strReq.find("/cmd") >=0:
            cmdline = strReq[strReq.find("/cmd")+5:-10].split('/')
            info = bithopper_global.pool.get_entry(cmdline[0])
            command = cmdline[1].lower()
            if command == 'incpenalty':
                info['penalty'] = info['penalty'] + 0.25
                bithopper_global.select_best_server()
            elif command == 'decpenalty':
                info['penalty'] = info['penalty'] - 0.25
                if info['penalty'] < 0.25:
                    info['penalty'] = 0.25
                bithopper_global.select_best_server()
            elif command == 'enable' and info['role'] != 'mine':
                info['role'] = 'mine'
                info['shares'] = 10**10
                bithopper_global.pool.update_api_servers()
                bithopper_global.select_best_server()
            elif command == 'force' and info['role'] != 'disable':
                bithopper_global.pool.Force(cmdline[0])
            elif command == 'disable' and info['role'] != 'disable':
                info['role'] = 'disable'
                info['forced'] = 0
                info['lag'] == False
                bithopper_global.select_best_server()
            
        # show stat
        if strReq.find("/current") >= 0:
            bithopper_global.log_dbg("Execute " + strReq)
            if strReq.find("index") >= 0:
                request.write(self.htmlString)
                request.finish()
                return server.NOT_DONE_YET
            else:
                response = json.dumps({"current":bithopper_global.pool.get_current(), 'mhash':bithopper_global.mHashes,
                    'btc_difficulty':bithopper_global.difficulty.get_btc_difficulty(),
                    'nmc_difficulty':bithopper_global.difficulty.get_nmc_difficulty(),
                    'servers':bithopper_global.pool.get_servers()})
                request.write(response)
                request.finish()
                return server.NOT_DONE_YET

        bithopper_global.new_server.addCallback(bitHopperLP, (request))
        return server.NOT_DONE_YET

    def render_POST(self, request):
        return bitHopper_Post(request)

    def getChild(self,name,request):
        if name == 'LP':
            return lpSite()
        return self

def parse_server_disable(option, opt, value, parser):
    setattr(parser.values, option.dest, value.split(','))

def main():
    
    parser = optparse.OptionParser(description='bitHopper')
    parser.add_option('--noLP', action = 'store_true' ,default=False, help='turns off client side longpolling')
    parser.add_option('--debug', action= 'store_true', default = False, help='Use twisted output')
    parser.add_option('--list', action= 'store_true', default = False, help='List servers')
    parser.add_option('--disable', type=str, default = None, action='callback', callback=parse_server_disable, help='Servers to disable. Get name from --list. Servera,Serverb,Serverc')
    parser.add_option('--port',type=int, default=8337, help='Listen port (default 8337)')
    args, rest = parser.parse_args()
    options = args
    bithopper_global.options = args
    
    servers = bithopper_global.pool.get_servers()

    if options.list:
        for k in servers:
            print k
        return
    
    for k in servers:
        servers[k]['user_shares'] = 0

    
    if options.disable != None:
        for k in options.disable:
            if k in servers:
                if servers[k]['role'] == 'backup':
                    print "You just disabled the backup pool. I hope you know what you are doing"
                servers[k]['role'] = 'disable'
            else:
                print k + " Not a valid server"

    
    # using database is default
    database.check_database(servers)

    if options.debug: log.startLogging(sys.stdout)
    site = server.Site(bitSite())
    reactor.listenTCP(options.port, site)
    tick_call = LoopingCall(bithopper_global.tick)
    tick_call.start(3)
    update_call = LoopingCall(bithopper_global.pool.update_api_servers)
    update_call.start( bithopper_global.pool.updateInterval )
    delag_call = LoopingCall(bithopper_global.delag_server)
    delag_call.start(119)
    info_call = LoopingCall(bithopper_global.recentInfo)
    info_call.start(120)
    
    reactor.run()

if __name__ == "__main__":
    main()
