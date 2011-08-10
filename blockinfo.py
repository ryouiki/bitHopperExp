#License#
# blockinfo.py is created by ryouiki and licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
# http://creativecommons.org/licenses/by-nc-sa/3.0/
# Based on a work at github.com.

from twisted.web.client import getPage
from twisted.internet.task import LoopingCall
import re
import calendar
import time

class Block:
    def __init__(self, number, stamp, poolName):
        self.number = number
        self.stamp = stamp
        self.trialBet = 0
        self.poolName = self.Filter(poolName)
    
    def Filter(self, poolName):
        if poolName.startswith('--') or poolName == 'N/A':
            poolName = ''
        else:
            poolName = poolName.lower()
        
        filters = { 'eligiusst':'eligius', 'bitcoinslc':'bitcoins.lc', 'minecoin':'mineco.in', 'mainframemc':'mainframe' }
        if poolName in filters:
            poolName = filters[poolName]
        
        return poolName
    
    def SetPool(self, poolName):
        poolName = self.Filter(poolName)
        
        # do not change to N/A or guesstimated pool name
        if self.poolName != '' and (poolName == '' or poolName.find(':') > 0):
            return 'notChanged', self.poolName
        
        # change guesstimated pool name with proper one
        if self.poolName.find(':') > 0 and poolName.find(':') < 0:
            if self.poolName.split(':')[0] == poolName:
                self.poolName = poolName
                return 'confirm', poolName
            else:
                priorName = self.poolName.split(':')[0]
                self.poolName = poolName
                return 'reject', priorName
        
        self.poolName = poolName
        
        minimumScore = { 'deepbit':75, 'btcguild':120, 'bitcoins.lc':150 }
        
        # if we guesstimated this block is from ABC pool
        if self.poolName.find(':') > 0:
            chance = self.poolName.split(':')
            if chance[0] in minimumScore:
                self.trialBet = float(chance[1]) / minimumScore[chance[0]]
                if self.trialBet>1.0:
                    return 'try', chance[0]
        
        return 'set', self.poolName

class BlockInfo:
    def __init__(self,bitHopper):
        self.bitHopper = bitHopper
        self.blocks = {}
        self.accuracy = {}
        self.digbtcUrl = 'http://digbtc.com/'
        self.pidentUrl = 'http://pident.artefact2.com/'
        self.lastGuessBlock = 0
        self.guessBlock = 0
        self.guessPool = ''
        self.digbtcRefreshRemain = 0
        self.pidentRefreshRemain = 0
        LoopingCall(self.Tick).start(30)
        LoopingCall(self.StartForced).start(5)
    
    def GetPoolInfo(self, poolName):
        return self.bitHopper.pool.get_entry(poolName)
    
    def Tick(self):
        blockNumberToDel = 0
        for blockNumber in self.blocks:
            self.bitHopper.log_msg('{0} : {1}sec : {2}'.format(blockNumber, int(time.time()-self.blocks[blockNumber].stamp), self.blocks[blockNumber].poolName))
            if (time.time() - self.blocks[blockNumber].stamp) > 7200:
                blockNumberToDel = blockNumber
        for acc in self.accuracy:
            if acc == 'bitcoins.lc' or acc == 'deepbit' or acc == 'btcguild':
                s = self.accuracy[acc]['success']
                f = self.accuracy[acc]['fail']
                c = self.accuracy[acc]['confirm']
                r = self.accuracy[acc]['reject']
                m = self.accuracy[acc]['miss']
                self.bitHopper.log_msg('{0} - s {1}, f {2} {3:.2%} / c {4}, r {5}, m {6} {7:.2%}'.format(acc, s, f, float(s)/(s+f+0.0000001), c, r, m, float(c)/(c+r+m+0.0000001)))
            
        if blockNumberToDel>0:
            del self.blocks[blockNumberToDel]
        #progress
        self.digbtcRefreshRemain -= 30
        self.pidentRefreshRemain -= 30
        
        if self.digbtcRefreshRemain <=0:
            self.FetchDigBtc()
        
        if self.pidentRefreshRemain <=0:
            self.FetchPident()

    def FetchDigBtc(self):
        self.digbtcRefreshRemain = 120   # every 2 minutes
        self.bitHopper.log_msg('BlockInfo Query - digbtc>')
        dig = getPage(self.digbtcUrl, timeout=10)
        dig.addCallback(self.ParseDigbtc)
        dig.addErrback(self.FetchErr)
    
    def FetchPident(self):
        self.pidentRefreshRemain = 30    # every 30 sec
        self.bitHopper.log_msg('BlockInfo Query - pident>')
        pid = getPage(self.pidentUrl, timeout=10)
        pid.addCallback(self.ParsePident)
        pid.addErrback(self.FetchErr)

    def FetchErr(self, failure = None):
        self.bitHopper.log_msg('BlockInfo Query failed : ' + str(failure))

    def StartForced(self):
        if self.guessBlock > self.lastGuessBlock:
            bet = self.blocks[self.guessBlock].trialBet
            self.bitHopper.log_msg('{0} force mine? with {1} bet'.format(self.guessBlock, bet))
            if self.bitHopper.get_progress(self.bitHopper.get_server()) > (0.43 / bet):
                self.lastGuessBlock = self.guessBlock
                if self.guessPool == 'deepbit':
                    self.bitHopper.pool.Force('deepbit', 500, True)
                elif self.guessPool == 'btcguild':
                    self.bitHopper.pool.Force('btcg', 900, True)
                #elif self.guessPool == 'bitcoins.lc':
                #    self.bitHopper.pool.Force('bclc', 1200, True)
        
        self.guessBlock = 0
        self.guessPool = ''
        

    def StopForced(self, poolLabel):
        self.bitHopper.log_msg('stop {0}'.format(poolLabel))
        if self.GetPoolInfo(poolLabel)['forced'] > 0:
            self.GetPoolInfo(poolLabel)['forced'] = 0
            self.bitHopper.select_best_server()
        else:
            self.bitHopper.log_msg('not mining {0} yet'.format(poolLabel) )

    def ParseDigbtc(self, digbtc):
        self.bitHopper.log_msg('BlockInfo Query - digbtc>>')
        outputs = re.finditer('<td>(2011[\- :0-9]+)</td>.*target=_blank>(\d+).*pool=[a-z\-\?]+>([a-z\-\?]+)</a></b>', digbtc)
        notIdentified = 0
        count = 0
        for output in outputs:
            count += 1
            stamp = calendar.timegm(time.strptime(output.group(1), "%Y-%m-%d %H:%M:%S"))
            passed = time.time() - stamp
            if passed < 7200: # < 2hours
                #print "{0} - {1} - {2} - {3}".format(passed, output.group(1),output.group(2), output.group(3))
                blockNumber = int(output.group(2))
                poolName = output.group(3)
                if blockNumber not in self.blocks:
                    self.blocks[blockNumber] = Block(blockNumber, stamp, poolName)
                    self.bitHopper.log_msg('new block {0}'.format(blockNumber))
                    notIdentified +=1
                else:
                    self.SetPoolName(blockNumber, poolName)
                    if self.blocks[blockNumber].poolName == '':
                        notIdentified +=1
        
        if count == 0 or notIdentified > 0:
            self.FetchPident()
                    
    def ParsePident(self, pident):
        self.bitHopper.log_msg('BlockInfo Query - pident>>')
        outputs = re.finditer("<tr>[\n\r]+<td>(.*)</td>[\n\r]+<td><a href='/b/(\d+)'.*[\n\r]+.*[sB]</td>\n<td>(.+)</td>[\n\r]+.*href='/(score.+)'>Score", pident)
        for output in outputs:
            stamp = output.group(1)
            blockNumber = int(output.group(2))
            poolName = output.group(3)
            if poolName != 'N/A':
                findName = re.search(";'>(.+)</span>", poolName)
                poolName = findName.group(1)
            scoreUrl = self.pidentUrl + output.group(4)
            
            if blockNumber not in self.blocks:
                if stamp.find('a few seconds ago') > -1 :
                    stamp = time.time() - 120    #regard as 2 minutes
                    self.blocks[blockNumber] = Block(blockNumber, stamp, poolName)
                    self.bitHopper.log_msg('new block {0}'.format(blockNumber))
                elif stamp.find('1 hour ago') > -1 :
                    stamp = time.time() - 1*60*60 + 180   #regard as 1 hour + 3 minutes
                    self.blocks[blockNumber] = Block(blockNumber, stamp, poolName)
                elif stamp.find('hour') > -1 :
                    match = re.search("(\d+) hou.+ and (\d+) min", stamp)
                    if match != None and int(match.group(1)) < 2:
                        elapsed = int(match.group(1))*60*60 - int(match.group(2))*60
                        if elapsed<7200:
                            stamp = time.time() - elapsed
                            self.blocks[blockNumber] = Block(blockNumber, stamp, poolName)
                elif stamp.find('a few minutes ago') > -1 :
                    stamp = time.time() - 10*60   #regard as 10 minutes
                    self.blocks[blockNumber] = Block(blockNumber, stamp, poolName)
                elif stamp.find('minute') > -1 :
                    match = re.search("(\d+) min", stamp)
                    stamp = time.time() - int(match.group(1))*60
                    self.blocks[blockNumber] = Block(blockNumber, stamp, poolName)

            #print "{0} - {1} - {2}".format(blockNumber, poolName,scoreUrl)
            if blockNumber in self.blocks:
                if self.blocks[blockNumber].poolName == '' and poolName == 'N/A':
                    queryScore = getPage(scoreUrl)
                    queryScore.addCallback(self.ParseScore, blockNumber)
                else:
                    self.SetPoolName(blockNumber, poolName)
                
                #print "{0} - stamp {1} - dig{2} pid{3} - scoreurl {4}".format(blockNumber, self.blocks[blockNumber].stamp, self.blocks[blockNumber].poolName, poolName, scoreUrl)
    
    def SetPoolName(self, blockNumber, poolName):
        cmd, name = self.blocks[blockNumber].SetPool(poolName)
        
        if name not in self.accuracy:
            self.accuracy[name] = { 'confirm':0, 'reject':0, 'success':0, 'fail':0, 'miss':0 }
        if self.blocks[blockNumber].poolName not in self.accuracy:
            self.accuracy[self.blocks[blockNumber].poolName] = { 'confirm':0, 'reject':0, 'success':0, 'fail':0, 'miss':0 }
        
        if cmd == 'reject':
            self.bitHopper.log_msg('reject guesstimated block {0} bet({3:.1f}) : not {1} but {2}'.format(blockNumber, name, self.blocks[blockNumber].poolName, self.blocks[blockNumber].trialBet))
            if self.blocks[blockNumber].trialBet > 1:
                self.accuracy[name]['fail'] += 1
            else:
                self.accuracy[name]['reject'] += 1
            self.accuracy[self.blocks[blockNumber].poolName]['miss'] += 1
            if self.lastGuessBlock == blockNumber:
                if name == 'btcguild':
                    self.StopForced('btcg')
                elif name == 'deepbit':
                    self.StopForced('deepbit')
                elif name == 'bitcoins.lc':
                    self.StopForced('bclc')
        elif cmd == 'confirm':
            self.bitHopper.log_msg('confirm guesstimated block {0} bet({2:.1f}) : {1}'.format(blockNumber, name, self.blocks[blockNumber].trialBet))
            if self.blocks[blockNumber].trialBet > 1:
                self.accuracy[name]['success'] += 1
            else:
                self.accuracy[name]['confirm'] += 1
        elif cmd == 'try' and self.guessBlock < blockNumber:
            if( time.time() - self.blocks[blockNumber].stamp < 1200):
                self.bitHopper.log_msg('try {0} - {1}'.format(blockNumber, name))
                self.guessBlock = blockNumber
                self.guessPool = name
    
    def ParseScore(self, scoreHtml, blockNumber):
        outputs = re.finditer("class='pool'.+;'>(.+)</span></td>[\n\r]+<td>([\.0-9]+)</td>", scoreHtml)
        maxChance = 0
        secondChance = 0
        bestGuess = ''
        for output in outputs:
            poolName = output.group(1)
            chance = float(output.group(2))
            if chance > maxChance:
                 secondChance = maxChance
                 maxChance = chance
                 bestGuess = poolName
            elif chance > secondChance:
                 secondChance = chance
        
        score = maxChance * ((maxChance/secondChance)-1)
        
        self.SetPoolName(blockNumber, "{0}:{1:.1f}:{2}:{3}".format(bestGuess, score*1000, str(maxChance), str(secondChance) ) )

