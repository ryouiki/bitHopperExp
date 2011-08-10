#License#
#bitHopper by Colin Rice is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#Based on a work at github.com.

import sqlite3
import datetime
import os

database = None
curs = None

def check_database(servers):
    print 'Checking Database'
    global database
    global curs
    
    #dbVersion = 1
    dbDir = os.path.dirname(os.path.abspath(__file__))
    #dbFile = os.path.join(dbDir, 'stats.v{0}.db'.format(dbVersion) )
    dbFile = os.path.join(dbDir, 'stats.db' )

    database = sqlite3.connect('stats.db')
    curs = database.cursor()
    
    for server_name in servers:
        sql = "CREATE TABLE IF NOT EXISTS "+server_name +" (time TIMESTAMP, diff REAL, shares INTEGER, myshares INTEGER, accept INTEGER, reject INTEGER)"
        curs.execute(sql)
        sql = "select accept from {0} ORDER BY accept desc limit 1".format(server_name)
        curs.execute(sql)
        fetch = curs.fetchone()
        accept = 0
        if fetch != None:
            accept = fetch[0]
        sql = "select reject from {0} ORDER BY reject desc limit 1".format(server_name)
        curs.execute(sql)
        fetch = curs.fetchone()
        reject = 0
        if fetch != None:
            reject = fetch[0]
        
        servers[server_name]['accept'] = accept
        servers[server_name]['reject'] = reject
        if 0 < (accept+reject):
            print '> db loaded : server {0} accept {1} reject {2}'.format(server_name, accept, reject)

def update_stat(server, share, difficulty, myshare, accept, reject):
    curs.execute('INSERT INTO {0} values(?, ?, ?, ?, ?, ?)'.format(server), (datetime.datetime.now(), difficulty, share, myshare, accept, reject) )
    database.commit()

