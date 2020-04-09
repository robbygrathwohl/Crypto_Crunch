import json
import time
import hashlib
import hmac

import string

import requests





class Poloniex(object):

    def __init__(self):
        config = json.load(open('config.json'))
        poloniex = config['poloniex']
        self.key = poloniex['key']
        self.secret = poloniex['secret']
        # print json.dumps(poloniex, sort_keys=True, indent=4, separators=(',', ': '))

    def test_api(self):
        # https://poloniex.com/public?command=returnTicker
        url = "https://poloniex.com/public?command=returnTicker"
        resp = requests.get(url, auth=(self.key, self.secret))
        print json.dumps(resp.json(), sort_keys=True, indent=4, separators=(',', ': '))

    def get_ticker(self, ticker):
        # https://poloniex.com/public?command=returnOrderBook&currencyPair=BTC_NXT&depth=10
        url = "https://poloniex.com/public?command=returnOrderBook&currencyPair=BTC_%s&depth=1" % ticker
        resp = requests.get(url, auth=(self.key, self.secret))
        # print json.dumps(resp.json(), sort_keys=True, indent=4, separators=(',', ': '))
        return resp.json()


class Bittrex(object):

    def __init__(self):
        config = json.load(open('config.json'))
        bittrex = config['bittrex']
        self.key = bittrex['key']
        self.secret = bittrex['secret']
        # print json.dumps(bittrex, sort_keys=True, indent=4, separators=(',', ': '))

    def test_api(self):
        # https://bittrex.com/api/v1.1/public/getmarkets
        url = "https://bittrex.com/api/v1.1/public/getmarkets"
        resp = requests.get(url, auth=(self.key, self.secret))
        print json.dumps(resp.json(), sort_keys=True, indent=4, separators=(',', ': '))

    def get_ticker(self, ticker):
        if ticker == "STR":
            ticker = "XLM"
        # https://bittrex.com/api/v1.1/public/getticker
        url = "https://bittrex.com/api/v1.1/public/getticker"
        # data={"market": "BTC-LTC"}
        resp = requests.get(url, data={"market": "BTC-%s" % ticker}, auth=(self.key, self.secret))
        # print json.dumps(resp.json(), sort_keys=True, indent=4, separators=(',', ': '))
        return resp.json()


class Exchange(object):

    def __init__(self):
        config = json.load(open('config.json'))

        poloniex = config['poloniex']
        self.poloniex_key = poloniex['key']
        self.poloniex_secret = poloniex['secret']
        self.poloniex_btc_wallet = ""
        self.poloniex_eth_wallet = ""
        self.poloniex_ltc_wallet = "LYTDmgTtYjDXTTzf9Jkezn6EyUU5BivYXz"

        bittrex = config['bittrex']
        self.key = bittrex['key']
        self.secret = bittrex['secret']

        self.bittrex_btc_wallet = "1KdfY4XK3LKjAkGwzbokpDPGX2gx2qCN9X"
        self.bittrex_eth_wallet = "0x5ea2d54d6c24a133a478c7a909f359d0d992e647" # Todo: OUTDATED INFO
        self.bittrex_ltc_wallet = "LZ21f8rDAkjVFnbDz9i9A6gU6vm5PaWU8R"

    def get_order_book(self, exchange_name, ticker, sell_or_buy):
        if exchange_name == "Bittrex":
            if ticker == "STR":
                ticker = "XLM"
            # https://bittrex.com/api/v1.1/public/getticker
            url = "https://bittrex.com/api/v1.1/public/getorderbook?market=BTC-" + ticker+"&type=both"
            # data={"market": "BTC-LTC"}
            resp = requests.post(url, auth=(self.key, self.secret))

            # print json.dumps(resp.json(), sort_keys=True, indent=4, separators=(',', ': '))
            if sell_or_buy == "sell":
                return resp.json()["result"]["buy"][0]["Rate"]
            if sell_or_buy == "buy":
                return resp.json()["result"]["sell"][0]["Rate"]

        if exchange_name == "Poloniex":
            if ticker == "XLM":
                ticker = "STR"
            url = "https://poloniex.com/public?command=returnOrderBook&currencyPair=BTC_" + ticker + "&depth=1"
            resp = requests.get(url, auth=(self.poloniex_key, self.poloniex_secret))

            if sell_or_buy == "sell":
                return resp.json()["bids"][0][0]
            if sell_or_buy == "buy":
                return resp.json()["asks"][0][0]


    #def transfer_assets(self, high, low):
    def asset_to_btc(self, ticker, exchange_name, amount):
        resp_rate = self.get_order_book(exchange_name, ticker, "sell")
        resp_rate = float(resp_rate)
        rate_str = '%.8f' % resp_rate

        if exchange_name == "Bittrex":
            if ticker == "STR":
                ticker = "XLM"
            url = "https://bittrex.com/api/v1.1/market/selllimit?apikey="+self.key+"&market=BTC-"+ticker+"&quantity="+str(amount)+"&rate="+rate_str+"&nonce={}".format(int(time.time()*10099999))
            sign = hmac.new(str(self.secret), url, hashlib.sha512)
            resp = requests.get(url, headers={"apisign": sign.hexdigest()}).json()
            if resp["success"] == True:
                print("Buy Order placed for BTC of the amount:   " + ('%.8f'%(amount * float(resp_rate)))+"\nTXID: "+ resp["result"]["uuid"])
                return amount * resp_rate
            else:
                print("ORDER FAILED")
                print(resp)
                exit()

        if exchange_name == "Poloniex":
            if ticker == "XLM":
                ticker = "STR"
            url = "https://poloniex.com/tradingApi?rate="+rate_str+"&amount="+str(amount)+"&currencyPair=BTC_"+ticker
            data = 'command=sell&nonce={}'.format(int(time.time() * 10099999))
            sign = hmac.new(self.poloniex_secret.encode(), data.encode(), digestmod=hashlib.sha512)
            headers = {"Content-Type": "application/x-www-form-urlencoded", "Sign": sign.hexdigest(),
                       "Key": self.poloniex_key, "Accept": "application/json"}
            resp = requests.post(url, data=data, headers=headers)

            # print "[DEBUG] %s" % resp.text
            print resp.status_code
            print resp.raw
            print resp.json()
            print("Buy Order placed for BTC of the amount:   " + ('%.8f' % (amount * resp_rate)) + "\nTXID: "
                  + resp.json()["resultingTrades"][0]["tradeID"])
            return amount * resp_rate


    def btc_to_asset(self, ticker, exchange_name, amount):
        resp_rate = self.get_order_book(exchange_name, ticker, "buy")
        resp_rate = float(resp_rate)
        rate_str = '%.8f' % resp_rate
        amount_str = '%.8f' % amount
        if exchange_name == "Bittrex":
            if ticker == "STR":
                ticker = "XLM"
            url = "https://bittrex.com/api/v1.1/market/buylimit?apikey="+self.key+"&market=BTC-"+ticker+"&quantity="+str(amount)+"&rate="+rate_str+"&nonce={}".format(int(time.time()*10099999))
            sign = hmac.new(str(self.secret), url, hashlib.sha512)
            resp = requests.get(url, headers={"apisign": sign.hexdigest()}).json()
            if resp["success"] == True:
                print("Buy Order placed for BTC of the amount:   " + ('%.8f' %(amount * float(resp_rate)))+"\nTXID: "
                      + resp["result"]["uuid"])
                return amount * resp_rate
            else:
                print("ORDER FAILED")
                exit()
        if exchange_name == "Poloniex":
            if ticker == "XLM":
                ticker = "STR"
            url = "https://poloniex.com/tradingApi"
            data = "command=buy&nonce={}".format(int(time.time() * 10099999))+\
                   "&rate="+rate_str+"&amount="+str(amount)+"&currencyPair=BTC_"+ticker
            # data = 'command=buy&nonce={}'.format(int(time.time() * 10099999))
            sign = hmac.new(self.poloniex_secret.encode(), data.encode(), digestmod=hashlib.sha512)
            headers = {"Content-Type": "application/x-www-form-urlencoded", "Sign": sign.hexdigest(),
                       "Key": self.poloniex_key, "Accept": "application/json"}
            resp = requests.post(url, data=data, headers=headers)

            # print "[DEBUG] %s" % resp.text
            print resp.status_code
            print resp.raw
            print resp.json()
            print("Buy Order placed for BTC of the amount:   " + ('%.8f'%(amount * resp_rate)) + "\nTXID: " + resp.json()["resultingTrades"][0]["tradeID"])
            return amount * resp_rate

    def ship_ltc(self, poor_exchange, rich_exchange, amount):
        pass

    def balance_assets(self, ticker):
        # TODO: Check the difference between poloniex and bittrex
        # TODO: Check Bittrex ticker price
        # ://bittrex.com/api/v1.1/account/getbalance?apikey=API_KEY&currency=BTC
        if ticker == "STR":
            ticker = "XLM"
        url = "https://bittrex.com/api/v1.1/account/getbalance?apikey="+self.key+"&currency="+ticker+"&nonce=1512127656"
        sign = hmac.new(str(self.secret), url, hashlib.sha512)
        # url = "https://bittrex.com/api/v1.1/account/getbalance?apikey=" + self.key + "&currency=" + ticker + "&nonce=1342342"
        resp = requests.get(url, headers={"apisign" : sign.hexdigest()})
        print json.dumps(resp.json(), sort_keys=True, indent=4, separators=(',', ': '))
        response_bittrex = resp.json()["result"]["Balance"]
        if ticker == "XLM":
            ticker = "STR"
        data = 'command=returnBalances&nonce={}'.format(int(time.time()*10099999))
        url = "https://poloniex.com/tradingApi"
        sign = hmac.new(self.poloniex_secret.encode(), data.encode(), digestmod = hashlib.sha512)
        resp = requests.post(url, data = data, headers={"Content-Type": "application/x-www-form-urlencoded", "Sign" : sign.hexdigest(), "Key" : self.poloniex_key})
        # print json.dumps(resp.json(), sort_keys=True, indent=4, separators=(',', ': '))
        # TODO: Transfer high to low LTC
        response_poloniex = resp.json()[ticker]
        traded_amount_in_BTC = 0
        poor_exchange = ""
        rich_exchange = ""
        if ticker == "DASH":
            if response_poloniex > response_bittrex:
                if response_bittrex < .015:
                    traded_amount_in_BTC=self.asset_to_btc(ticker, "Poloniex", .1 - response_bittrex)
                    poor_exchange="Bittrex"
                    rich_exchange = "Poloniex"
            elif response_bittrex > response_poloniex:
                if response_poloniex < .015:
                    traded_amount_in_BTC=self.asset_to_btc(ticker, "Bittrex", .1 - response_poloniex)
                    poor_exchange = "Poloniex"
                    rich_exchange = "Bittrex"
        if ticker == "LTC":
            if response_poloniex > response_bittrex:
                if response_bittrex < .05:
                    traded_amount_in_BTC=self.asset_to_btc(ticker, "Poloniex", .3 - response_bittrex)
                    poor_exchange = "Bittrex"
                    rich_exchange = "Poloniex"
            elif response_bittrex > response_poloniex:
                if response_poloniex < .05:
                    traded_amount_in_BTC=self.asset_to_btc(ticker, "Bittrex", .3 - response_poloniex)
                    poor_exchange = "Poloniex"
                    rich_exchange = "Bittrex"
        if ticker == "STR":
            if response_poloniex > response_bittrex:
                if response_bittrex < 100:
                    traded_amount_in_BTC = self.asset_to_btc(ticker, "Poloniex", 500 - response_bittrex)
                    poor_exchange = "Bittrex"
                    rich_exchange = "Poloniex"
            elif response_bittrex > response_poloniex:
                if response_poloniex < 100:
                    traded_amount_in_BTC = self.asset_to_btc(ticker, "Bittrex", 500 - response_poloniex)
                    poor_exchange = "Poloniex"
                    rich_exchange = "Bittrex"

        # TODO: Purchase BTC with LTC

        # self.ship_ltc(poor_exchange, rich_exchange, traded_amount_in_BTC)
        # TODO: Purchase original **ticker** with LTC
        pass

    def buy_asset(self, exchange_name, ticker, amount):
        # TODO: Purchase Coin on Exchange

        if exchange_name == "Poloniex":
            # TODO: Purchase Poloniex
            pass
        elif exchange_name == "Bittrex":
            # TODO: Purchase Bittrex
            pass
        pass

    def sell_asset(self, exchange_name, ticker, amount):
        # TODO: Sell Coin on Exchange

        if exchange_name == "Poloniex":
            # TODO: Sell Poloniex
            pass
        elif exchange_name == "Bittrex":
            # TODO: Sell Bittrex
            pass
        pass


def main(ticker):

    # ticker = "ETH"  # Will come from ML
    amount = 0  # TODO CHANGE THIS!!!
    if ticker == "DASH":
        amount = .008
    elif ticker == "LTC":
        amount = .01
    elif ticker == "STR":
        amount = 65


    exchange = Exchange()
    exchange.balance_assets(ticker)
    # print "Poloniex"
    poloniex = Poloniex()
    # poloniex.test_api()
    poloniex_ob = poloniex.get_ticker(ticker)  # Poloniex Order Book

    # print "\n\n\n"

    # print "Bittrex"
    bittrex = Bittrex()
    # bittrex.test_api()
    bittrex_ob = bittrex.get_ticker(ticker)  # Bittrex Order Book

    # print "\n\n\n"

    # Compare Exchanges
    print "Ticker: %s" % ticker

    poloniex_ask = poloniex_ob["asks"][0][0]
    print "Poloniex Ask: %s" % poloniex_ask
    if ticker == "STR":
        ticker = "XLM"
    bittrex_ask = bittrex_ob["result"]["Ask"]
    print "Bittrex Ask: %s" % bittrex_ask

    print ""

    if ticker == "XLM":
        ticker = "STR"
    poloniex_bid = float(poloniex_ob["bids"][0][0])
    print "Poloniex Bid: %s" % poloniex_bid
    if ticker == "STR":
        ticker = "XLM"
    bittrex_bid = float(bittrex_ob["result"]["Bid"])
    print "Bittrex Bid: %s" % bittrex_bid

    print ""
    if ticker == "XLM":
        ticker = "STR"
    bid_comp = bittrex_bid - poloniex_bid

    poloniex_fee = 0.0025
    bittrex_fee = 0.0025
    total_fee = poloniex_fee + bittrex_fee

    if bid_comp < 0:
        poloniex_bid_percent = abs(bid_comp) / poloniex_bid

        print "Poloniex High"
        print "Percent Change: %s" % (float(poloniex_bid_percent) * 100)
        print "Poloniex_bid_percent " + str(poloniex_bid_percent)
        print "total_fee_percent " + str(total_fee)
        if poloniex_bid_percent > total_fee:
            print "Sell on Poloniex"
            percent_gains = poloniex_bid_percent - total_fee
            print "Percent Gain: %s" % (float(percent_gains) * 100)
            # TODO: Invoke Sell Poloniex
            exchange.asset_to_btc(ticker, "Poloniex", amount)
            # TODO: Invoke Buy Bittrex
            if ticker == "STR":
                ticker = "XLM"
            exchange.btc_to_asset(ticker, "Bittrex",  amount)
            if ticker == "XLM":
                ticker = "STR"
        else:
            print "Hold on Poloniex"
    else:
        bittrex_bid_percent = abs(bid_comp) / bittrex_bid
        print "bittrex_bid_percent " + str(bittrex_bid_percent)
        print "total_fee_percent " + str(total_fee)
        print "Bittrex High"
        print "Percent Change: %s" % (float(bittrex_bid_percent) * 100)

        if bittrex_bid_percent > total_fee:
            print "Sell on Bittrex"
            percent_gains = bittrex_bid_percent - total_fee
            print "Percent Gain: %s" % (float(percent_gains) * 100)
            # TODO: Invoke Sell Bittrex
            if ticker == "STR":
                ticker = "XLM"
            exchange.asset_to_btc(ticker, "Bittrex", amount)
            # TODO: Invoke Buy Poloniex
            if ticker == "XLM":
                ticker = "STR"
            exchange.btc_to_asset(ticker, "Poloniex", amount)

        else:
            print "Hold on Bittrex"

    print("\n\n\n")

countdown = 150
ticker_values = ["DASH", "LTC", "STR"]
while True:
    #print("COUNTDOWN " + str(countdown))
    if(countdown < 0):
        #print("[INFO] - COUNTDOWN is ZERO")
        ticker_values = []
        f = open("tmp.txt")
        for line in f:
            ticker_values.append(line.strip())
        if ticker_values[0] == "IDLE":
            ticker_values = ["DASH", "LTC", "STR"]
        print("[INFO] - Using Ticker Values: " + str(ticker_values))
        countdown = 2
    for i in range(len(ticker_values)):
        main(ticker_values[i])
        time.sleep(2)
        countdown=countdown - 1