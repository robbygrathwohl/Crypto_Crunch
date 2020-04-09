# Handoff: A String of either: [STR, LTC, ETH, IDLE]

# Imports
import pandas as pd
from datetime import timedelta
from datetime import datetime
from sklearn.model_selection import train_test_split
import xgboost as xgb
import time
###############################################
## GLOBAL VARIABLES ##
models = {}
altcoins = ['STR', 'LTC', 'DASH']
altcoin_data = {}

def get_json_data(json_url):
    # Download JSON data, return as a dataframe.
    print('Downloading {}'.format(json_url))
    df = pd.read_json(json_url)
    return df

## This Function is used to gather the data for training the model
def get_crypto_data(poloniex_pair, base_polo_url, start_date, end_date, period):
    '''Retrieve cryptocurrency data from poloniex'''
    json_url = base_polo_url.format(poloniex_pair, start_date.timestamp(), end_date.timestamp(), period)
    data_df = get_json_data(json_url)
    data_df = data_df.set_index('date')
    return data_df

### Function to run XGBoost ###
# Made with reference from: https://www.kaggle.com/sudalairajkumar/two-sigma-connect-rental-listing-inquiries/xgb-starter-in-python
def runXGB(train_X, train_y, test_X, test_y=None, feature_names=None, seed_val=0, num_rounds=100):
    param = {}
    param['objective'] = 'reg:linear'
    param['eta'] = .05
    param['max_depth'] = 6
    param['silent'] = 0

    num_rounds = num_rounds
    
    plist = list(param.items())
    xgtrain = xgb.DMatrix(train_X, train_y)

    if test_y is not None:
        xgtest = xgb.DMatrix(test_X, label=test_y)
        watchlist = [(xgtrain, 'train'), (xgtest, 'test')]
        model = xgb.train(plist, xgtrain, num_rounds, watchlist, early_stopping_rounds=20)
    else:
        xgtest = xgb.DMatrix(test_X)
        model = xgb.train(plist, xgtrain, num_rounds)
        
    pred_test_y = model.predict(xgtest)
    return pred_test_y, model


# Function must be called to initialize the models for the currencies

def init_models():
	global models
	global altcoins
	global altcoin_data
	base_polo_url = 'https://poloniex.com/public?command=returnChartData&currencyPair={}&start={}&end={}&period={}'
	start_date = datetime.strptime('2018-12-01', '%Y-%m-%d') # get data from the start of 2018
	end_date = datetime.now() # up until today
	period = 300 # pull daily data (86,400 seconds per day)
	for altcoin in altcoins:
		coinpair = 'BTC_{}'.format(altcoin)
		print(coinpair)
		crypto_price_df = get_crypto_data(coinpair, base_polo_url, start_date, end_date, period)
		print('Finished Downloading')
		df = crypto_price_df.drop(['close','high','low','open','quoteVolume'],axis=1)
		v1 = list(map((lambda x : ((df['weightedAverage']).iloc[x:x+6]).std()), range(len(df),0, -1)))
		print('Calculated V1')
		v2 = list(map((lambda x : ((df['weightedAverage']).iloc[x+6:x+12]).std()), range(len(df),0, -1)))
		print('Calculated V2')
		v3 = list(map((lambda x : ((df['weightedAverage']).iloc[x+12:x+18]).std()), range(len(df),0,-1)))
		print('Calculated V3')
		v4 = list(map((lambda x : ((df['weightedAverage']).iloc[x+18:x+24]).std()), range(len(df),0,-1)))
		print('Calculated V4')
		v5 = list(map((lambda x : ((df['weightedAverage']).iloc[x+24:x+30]).std()), range(len(df),0,-1)))
		print('Calculated V5')
		v6 = list(map((lambda x : ((df['weightedAverage']).iloc[x+30:x+36]).std()), range(len(df),0,-1)))
		print('Calculated V6')
		v7 = list(map((lambda x : ((df['weightedAverage']).iloc[x+36:x+42]).std()), range(len(df),0,-1)))
		print('Calculated V7')
		v8 = list(map((lambda x : ((df['weightedAverage']).iloc[x+42:x+48]).std()), range(len(df),0,-1)))
		print('Calculated V8')
		dfv = df.iloc[48:,:]
		dfv = dfv.assign(volatility_1=pd.Series(v1[48:], index=dfv.index))
		dfv = dfv.assign(volatility_2=pd.Series(v2[48:], index=dfv.index))
		dfv = dfv.assign(volatility_3=pd.Series(v3[48:], index=dfv.index))
		dfv = dfv.assign(volatility_4=pd.Series(v4[48:], index=dfv.index))
		dfv = dfv.assign(volatility_5=pd.Series(v5[48:], index=dfv.index))
		dfv = dfv.assign(volatility_6=pd.Series(v6[48:], index=dfv.index))
		dfv = dfv.assign(volatility_7=pd.Series(v7[48:], index=dfv.index))
		dfv = dfv.assign(volatility_8=pd.Series(v8[48:], index=dfv.index))
		y = list(map((lambda x : ((df['weightedAverage']).iloc[x+1:x+7]).std()*1000000000), range(0,len(df))))
		y = y[48:]
		y = pd.DataFrame(y)
		y = y.dropna()
		if(len(y) < len(dfv)):
			dfv = dfv.iloc[:len(y),:]
		train_X, test_X, train_y, test_y = train_test_split(dfv,y,test_size=0.25)
		preds, model = runXGB(train_X, train_y, test_X)
		models[altcoin] = model
		altcoin_data[altcoin] = dfv

# Start of main function
def learn():
	global models
	global altcoins
	global altcoin_data
	base_polo_url = 'https://poloniex.com/public?command=returnChartData&currencyPair={}&start={}&end={}&period={}'
	# Valid periods: 300, 900, 1800, 7200, 14400, and 86400
	period = 300 # pull daily data (86,400 seconds per day)
	#altcoins = ['STR', 'LTC', 'ETH']
	#altcoin_data = {}
	file = "tmp.txt"
	threshold = 150
	hot = 0
	f = open(file, 'w')
	for altcoin in altcoins:
		coinpair = 'BTC_{}'.format(altcoin)
		now = datetime.now()
		earlier = (datetime.now() - timedelta(minutes=5))
		print(coinpair)
		crypto_price_df = get_crypto_data(coinpair, base_polo_url, earlier, now, period)
		new_entry = crypto_price_df.drop(['close','high','low','open','quoteVolume'],axis=1)
		dfv = pd.DataFrame(altcoin_data[altcoin])
		w1 = dfv['weightedAverage'].iloc[-6:].std()
		w2 = dfv['weightedAverage'].iloc[-12:-6].std()
		w3 = dfv['weightedAverage'].iloc[-18:-12].std()
		w4 = dfv['weightedAverage'].iloc[-24:-18].std()
		w5 = dfv['weightedAverage'].iloc[-30:-24].std()
		w6 = dfv['weightedAverage'].iloc[-36:-30].std()
		w7 = dfv['weightedAverage'].iloc[-42:-36].std()
		w8 = dfv['weightedAverage'].iloc[-48:-42].std()
		new_entry = new_entry.assign(volatility_1=w1)
		new_entry = new_entry.assign(volatility_2=w2)
		new_entry = new_entry.assign(volatility_3=w3)
		new_entry = new_entry.assign(volatility_4=w4)
		new_entry = new_entry.assign(volatility_5=w5)
		new_entry = new_entry.assign(volatility_6=w6)
		new_entry = new_entry.assign(volatility_7=w7)
		new_entry = new_entry.assign(volatility_8=w8)
		result = models[altcoin].predict(xgb.DMatrix(new_entry))
		dfv = dfv.append(new_entry)
		altcoin_data[altcoin] = dfv
		if(result > threshold):
			print('Writing ' + str(altcoin))
			f.write(altcoin + "\n")
			hot = hot + 1
	if(hot == 0):
		print('Writing IDLE')
		f.write('[IDLE]')
	f.close()
init_models()
while(True):
	learn()
	time.sleep(60)
	




