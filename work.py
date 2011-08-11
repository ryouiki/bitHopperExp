#License#
#bitHopper by Colin Rice is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#Based on a work at github.com.

import json
import socket
import os
import base64
import exceptions
import time


from zope.interface import implements

from twisted.web.iweb import IBodyProducer
from twisted.web.http_headers import Headers
from twisted.internet import defer
from twisted.internet.defer import succeed, Deferred
from twisted.internet.protocol import Protocol

i = 1

class StringProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)
    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

class WorkProtocol(Protocol):

    def __init__(self, finished):
        self.data = ""
        self.finished = finished
    
    def dataReceived(self, data):
        self.data += data

    def connectionLost(self, reason):
        self.finished.callback(self.data)

def print_error(x):
    print x

@defer.inlineCallbacks
def jsonrpc_lpcall(agent,server, url, update):
    
    global i
    request = json.dumps({'method':'getwork', 'params':[], 'id':i}, ensure_ascii = True)
    i = i +1
    
    header = {'Authorization':["Basic " +base64.b64encode(server['user']+ ":" + server['pass'])], 'User-Agent': ['poclbm/20110709'],'Content-Type': ['application/json'] }
    d = agent.request('GET', "http://" + url, Headers(header), None)
    d.addErrback(print_error)
    body = yield d
    d = update(body)

@defer.inlineCallbacks
def get(agent,url):
    header = {'User-Agent': ['Opera/9.02 (Windows NT 5.1; U; en)'],'Content-Type': ['application/x-www-form-urlencoded'] }
    d = agent.request('GET', url, Headers(header), None)
    response = yield d
    finish = Deferred()
    response.deliverBody(WorkProtocol(finish))
    body = yield finish
    defer.returnValue(body)

@defer.inlineCallbacks
def get_btcmp(agent, url):
    header = {'User-Agent': ['Opera/9.02 (Windows NT 5.1; U; en)'],'Content-Type': ['application/x-www-form-urlencoded'], 'Cookie': ['session_id=1234'] }
    d = agent.request('POST', url, Headers(header), StringProducer('_token=1234'))
    response = yield d
    finish = Deferred()
    response.deliverBody(WorkProtocol(finish))
    body = yield finish
    defer.returnValue(body)

@defer.inlineCallbacks
def jsonrpc_call(agent, server, data , set_lp):
    global i
    try:
        request = json.dumps({'method':'getwork', 'params':data, 'id':i}, ensure_ascii = True)
        i = i +1
        
        header = {'Authorization':["Basic " +base64.b64encode(server['user']+ ":" + server['pass'])], 'User-Agent': ['poclbm/20110709'],'Content-Type': ['application/json'] }
        d = agent.request('POST', "http://" + server['mine_address'], Headers(header), StringProducer(request))
        response = yield d
        header = response.headers
        #Check for long polling header
        if set_lp != None and set_lp(None, True):
            for k,v in header.getAllRawHeaders():
                if k.lower() == 'x-long-polling':
                    set_lp(v[0])
                    break

        finish = Deferred()
        response.deliverBody(WorkProtocol(finish))
        body = yield finish
    except Exception, e:
        print 'Caught, jsonrpc_call insides on {0}'.format(server['name'])
        print e
        defer.returnValue(None)

    try:
        message = json.loads(body)
        value =  message['result']
        defer.returnValue(value)
    except Exception, e:
        print "Error in json decoding, Server probably down on {0}".format(server['name'])
        print body
        defer.returnValue(None)

@defer.inlineCallbacks
def jsonrpc_getwork(bitHopper, serverKey, data, j_id, request):
    new_server = bitHopper.get_new_server
    set_lp = bitHopper.lp.set_lp
    agent = bitHopper.json_agent
    server = bitHopper.pool.get_entry(serverKey)
    try:
        work = yield jsonrpc_call(agent, server,data,set_lp)
    except Exception, e:
            bitHopper.log_dbg( 'caught, first response/writing on {0}'.format(server['name']) )
            bitHopper.log_dbg( e )
            work = None

    i = 1
    while work == None:
        i += 1
        if data == []:
            server = new_server(server)
        try:
            if i > 4:
                time.sleep(0.1)
            work = yield jsonrpc_call(agent, server,data,set_lp)
        except Exception, e:
            bitHopper.log_dbg( 'caught, inner jsonrpc_call loop on {0}'.format(server['name']) )
            bitHopper.log_dbg( e )
            work = None
            continue

    try:
    	strWork = str(work)
        if strWork=='True':
            # result : share accepted
            server['accept'] = server['accept'] + 1
            server['my_round_share'] = server['my_round_share'] +1
        elif strWork=='False':
            # result : share rejected
            server['reject'] = server['reject'] + 1
        else:
            # result : getwork
            merkle_root = work["data"][72:136]
            bitHopper.getwork_store.add(serverKey,merkle_root)

        response = json.dumps({"result":work,'error':None,'id':j_id})
        request.write(response)
        request.finish()
    except Exception, e:
        print 'caught, Final response/writing on {0}'.format(server['name'])
        print e
