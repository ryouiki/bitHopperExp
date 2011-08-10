#License#
#bitHopper by Colin Rice is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
#Based on a work at github.com.

import urllib2

class Difficulty():
    def __init__(self,bitHopper):
        self.bitHopper = bitHopper
        self.btc_difficulty = 1690906.2047244
        self.nmc_difficulty = 94037.96

    def get_btc_difficulty(self):
        return self.btc_difficulty

    def get_nmc_difficulty(self):
        return self.nmc_difficulty

    def update_difficulty(self):
        try:
            req = urllib2.Request('http://blockexplorer.com/q/getdifficulty')
            response = urllib2.urlopen(req)
            new_diff = float(response.read())
            if self.btc_difficulty != new_diff:
                self.btc_difficulty = new_diff
                self.bitHopper.log_msg("BTC difficulty changed : " + str(new_diff))
        except:
            pass

        try:
            req = urllib2.Request('http://namebit.org/')
            response = urllib2.urlopen(req)
            htmlpage = response.read()
            output = re.search("difficulty\">([0-9\.]*)</td>", htmlpage)
            if output != None:
                new_diff = float(output.group(1))
                if self.nmc_difficulty != new_diff:
                    self.nmc_difficulty = new_diff
                    self.bitHopper.log_msg("NMC difficulty changed  : " + str(new_diff))
        except:
            pass

