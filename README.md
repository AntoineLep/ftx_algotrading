# FTX Algotrading

[![Made With Python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![GitHub License](https://img.shields.io/github/license/AntoineLep/ftx_algotrading)](https://github.com/AntoineLep/ftx_algotrading/blob/main/LICENSE)

FTX Algotrading is a simple algorithmic trading strategy runner for FTX.

The project aims to provide an environment and tools for developing automatic trading strategies. It comes with a 
simple framework that can be used to automatically retrieve OHLC data within several timeframes, compute technical
indicators and setup managed position on [FTX exchange](https://ftx.com/).

This project comes with some [built-in strategies](https://github.com/AntoineLep/ftx_algotrading/tree/main/strategies).
Don't hesitate to take a look at it to better understand how the project works.

## Table of contents

- [Get started](#get-started)
- [Documentation](#documentation)
  - [Create a strategy](#create-a-strategy)
  - [Launch stock data acquisition](#launch-stock-data-acquisition)
  - [Retrieve and manipulate acquired data](#retrieve-and-manipulate-acquired-data)
  - [Technical indicators](#technical-indicators)
  - [Position driver](#position-driver)
  - [FTX Api](#ftx-api)
  - [Static configuration](#static-configuration)
    - [Display / hide data acquisition logs](#display--hide-data-acquisition-logs)
    - [Disable / enable automatically computed technical indicators](#disable--enable-automatically-computed-technical-indicators)
- [Strategies](#strategies)
  - [Existing strategies](#existing-strategies)
  - [Create your own](#create-your-own)
- [Disclaimer](#disclaimer)
- [Credits](#credits)


## Get started

Open `config/` folder and fill the `private/` folder with a new file called `ftx_config.py` with your ftx api key
info. A template is given in this directory with some basic config info about ftx exchange and how to structure the
configuration file.

```python
ws_endpoint = "wss://ftx.com/ws/"
rest_endpoint = "https://ftx.com/api/"

api = {
    "key": "YOUR API KEY HERE",
    "secret": "YOUR API SECRET HERE",
    "sub_account": "YOUR SUB ACCOUNT NAME HERE"
}
```

`config/application_config.py` allows configuring what strategy to run. It also permits setting up log path and level.


```python
from strategies.demo_strategy.demo_strategy import DemoStrategy

strategy = DemoStrategy()

log = {
    "level": "info",
    "path": "logs"
}
```

## Documentation

### Create a strategy

Strategies are stored into `strategies/` folder.

Let's create a `demo_strategy` to illustrate this documentation:

- Create a `strategies/demo_strategy` folder
- Create the strategy file `strategies/demo_strategy/demo_strategy.py`

All strategies must extend the
[Strategy](https://github.com/AntoineLep/ftx_algotrading/blob/main/core/strategy/strategy.py)
class. Here is a minimum working strategy code:

```python
import logging
import time

from core.strategy.strategy import Strategy


class DemoStrategy(Strategy):
    """The demo strategy"""

    def __init__(self):
        """The demo strategy constructor"""
        
        logging.info("DemoStrategy run strategy")
        super(DemoStrategy, self).__init__()

    def before_loop(self) -> None:
        """Called before each loop"""
        
        logging.info("DemoStrategy before_loop")
        pass

    def loop(self) -> None:
        """The strategy core loop method"""
        
        logging.info("DemoStrategy loop")
        pass

    def after_loop(self) -> None:
        """Called after each loop"""
        
        logging.info("DemoStrategy after_loop")
        time.sleep(10)  # Sleep 10 sec

    def cleanup(self) -> None:
        """Clean strategy execution"""
        
        logging.info("DemoStrategy cleanup")
```

A strategy is structured around 5 key methods. It works this way:

`__init__` is called first as it's the class constructor, then the strategy runner will call indefinitely `before_loop`,
`loop` and `after_loop`. When a blocking exception is raised or when the program is getting killed, `cleanup` is called.

- `__init__` contains your strategy initialization logics. You can set up FTX data acquisition, initialize vars or
  whatever
- `before_loop` is called before each strategy loop. You can use it to ensure all is ready for the loop core method
- `loop` is the strategy loop core method where you will most likely put the core logics of your strategy. Market data
  checks, wallet balance recovery, decide to open or not a position and drive opened position for example are logics to
  be put into this method
- `after_loop` is called after each strategy loop. You can use it to clean anything you used in the loop core method and
  to make your strategy sleep a bit before the next loop
- `cleanup` contains your strategy cleanup logics. You can delete file, close position or whatever

### Launch stock data acquisition

In order to launch stock data acquisition, you will need a
[FtxRestApi](https://github.com/AntoineLep/ftx_algotrading/blob/main/core/ftx/rest/ftx_rest_api.py)
instance, a trading pair (`BTC-PERP` for example), and the different timeframes you want to retrieve data on.

Timeframes are expressed in seconds and supported values are: [15, 60, 300, 900, 3600, 14400, 86400]

You can launch as many data acquisitions as you want on several coins as long as it doesn't exceed
[FTX API rate limits](https://help.ftx.com/hc/en-us/articles/360052595091-Ratelimits-on-FTX) 

Let's add some logic to the `demo_strategy` developed in the [Create a strategy](#create-a-strategy) section to launch
background data acquisition for `BTC-PERP` on 15 sec and 60 sec timeframes:

Add the following imports:

```python
from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.stock.crypto_pair_manager import CryptoPairManager
```

In the `__init__` method, launch data acquisition:

```python
def __init__(self):
    """The demo strategy constructor"""
    
    logging.info("DemoStrategy run strategy")
    super(DemoStrategy, self).__init__()

    self.ftx_rest_api: FtxRestApi = FtxRestApi()
    self.btc_pair_manager: CryptoPairManager = CryptoPairManager("BTC-PERP", self.ftx_rest_api)
    self.btc_pair_manager.add_time_frame(15)
    self.btc_pair_manager.add_time_frame(60)
    self.btc_pair_manager.start_all_time_frame_acq()
```

In the `cleanup` method, stop data acquisition:

```python
def cleanup(self) -> None:
    """Clean strategy execution"""
    
    logging.info("DemoStrategy cleanup")
    self.btc_pair_manager.stop_all_time_frame_acq()
```

Launch the bot and see the data acquisition being done in front of your eyes.

> :warning: After starting the acquisition, the last MAX_ITEM_IN_DATA_SET will be retrieved
> (see in [StockDataManager](https://github.com/AntoineLep/ftx_algotrading/blob/main/core/stock/stock_data_manager.py)).
> Older data points will be removed from the system as the acquisition continues. If you want to retrieve more than this
> amount of data, store it in your strategy or update the global MAX_ITEM_IN_DATA_SET value.

### Retrieve and manipulate acquired data

Acquired data are OHLCV (Open, High, Low, Close, Volume) points used to represent candles in candlestick charts. The
[Candle](https://github.com/AntoineLep/ftx_algotrading/blob/main/core/models/candle.py)
class provide OHLCV values for each point in addition to some helpers that identify candle patterns such as 
[hammer](https://candlecharts.com/candlestick-patterns/hammer-pattern/),
[hanging man](https://candlecharts.com/candlestick-patterns/hanging-man-pattern/),
[inverted hammer](https://candlecharts.com/candlestick-patterns/inverted-hammer-pattern/) or
[shooting star](https://candlecharts.com/candlestick-patterns/shooting-star-pattern/).

Let's continue to work on the `demo_strategy` developed in the [Create a strategy](#create-a-strategy) section after we
succeeded to [Launch stock data acquisition](#launch-stock-data-acquisition). We will now display some information about
the last data points.

Add the following imports:

```python
from core.stock.stock_data_manager import StockDataManager
from core.models.candle import Candle
```

In the `loop` method, read last data point and display last 3 data points average volume:

```python
def loop(self) -> None:
    """The strategy core loop method"""
    
    logging.info("DemoStrategy loop")
    
    stock_data_manager: StockDataManager = self.btc_pair_manager.get_time_frame(15).stock_data_manager
    
    # Display last candle info
    if len(stock_data_manager.stock_data_list) > 1:
        last_candle: Candle = stock_data_manager.stock_data_list[-1]

        logging.info(f"Last candle open price: {last_candle.open_price}")
        logging.info(f"Last candle high price: {last_candle.high_price}")
        logging.info(f"Last candle low price: {last_candle.low_price}")
        logging.info(f"Last candle close price: {last_candle.close_price}")
        logging.info(f"Last candle volume: {last_candle.volume}")
        logging.info(f"Last candle is a hammer or a hanging man: {last_candle.is_hammer_or_hanging_man()}")

    # Display last 3 candles average volume
    if len(stock_data_manager.stock_data_list) > 3:
        last_3_candle_volumes = sum([d.volume for d in stock_data_manager.stock_data_list[-3:]])
        logging.info(f"Last 3 candles average volume: {last_3_candle_volumes / 3}")
```

### Technical indicators

Technical indicators are automatically computed after each data acquisition (See 
[Disable / enable automatically computed technical indicators](#disable--enable-automatically-computed-technical-indicators)
if needed).
We use
[stockstats](https://pypi.org/project/stockstats/0.4.1/) library that supply a wrapper StockDataFrame for 
pandas.DataFrame with inline stock statistics/indicators support. 

There are plenty of indicators supported, the documentation is clear, and the library is quite easy to handle. Here is a
basic example of how to update the `demo_strategy` to display the last RSI (Relative Strength Index) values:

Add the following import:

```python
import stockstats
```

In the `loop` method, add this code to read RSI stockstats values:

```python
stock_data_manager: StockDataManager = self.btc_pair_manager.get_time_frame(15).stock_data_manager

# Use stockstats to display RSI_14 indicator values
indicators_dataframe: stockstats.StockDataFrame = stock_data_manager.stock_indicators
if indicators_dataframe is not None:
    logging.info(indicators_dataframe['rsi'])
```

### Position driver

> Full doc coming very soon

You can use the PositionDriver class to run position with automated management. It allows creating simple position
opening setup with trigger orders for taking profit or stopping losses.

![image](https://user-images.githubusercontent.com/6230724/119690499-0a9f4700-be4a-11eb-92f7-7259a13eedc2.png)

### FTX Api

### Static configuration

#### Display / hide data acquisition logs

When you have a lot of data to acquire, it can be better to not display logs since there are not necessarily relevant.
Default value for this configuration is `True`.

````python
from core.stock.time_frame_manager import TimeFrameManager

# Deactivate stock data log for readability purposes
TimeFrameManager.log_received_stock_data = False
````

#### Disable / enable automatically computed technical indicators

When a timeframe is running and acquiring data, the default behaviour is to compute and refresh a bunch of technical 
indicators on each candle retrieved. If this is not needed, this behaviour can be disabled for performance purposes.
When adding a timeframe to a given
[CryptoPairManager](https://github.com/AntoineLep/ftx_algotrading/blob/main/core/stock/crypto_pair_manager.py),
set `auto_compute_indicators` option to `False`. Example:

```python
from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.stock.crypto_pair_manager import CryptoPairManager

ftx_rest_api: FtxRestApi = FtxRestApi()
btc_pair_manager: CryptoPairManager = CryptoPairManager("BTC-PERP", self.ftx_rest_api)
btc_pair_manager.add_time_frame(15, False)
btc_pair_manager.start_all_time_frame_acq()
```

## Strategies

### Existing strategies

| Name                                                                                                                                                                                | Purpose                                                                                                                                                                                                                                                                                                                                                                        |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [twitter_elon_musk_doge_tracker](https://github.com/AntoineLep/ftx_algotrading/blob/main/strategies/twitter_elon_musk_doge_tracker/twitter_elon_musk_doge_tracker.py)               | Track abnormal `DOGE-PERP` volume increase when Elon Musk tweet something. This strategy has an internal `config/private/twitter_config.py` file that has to be created before being able to run it. As for `ftx_config.py`, it comes with a template. Make sure to use x20 leverage on your sub account before using this strategy (account > settings > margin) |
| [listing_sniper](https://github.com/AntoineLep/ftx_algotrading/blob/main/strategies/listing_sniper/listing_sniper.py)                                                               | A strategy to snipe a given pair listing by brute forcing a buy position on it until it passes.                                                                                                                                                                                                                                                                                |
| [multi_coin_abnormal_volume_tracker](https://github.com/AntoineLep/ftx_algotrading/blob/main/strategies/multi_coin_abnormal_volumes_tracker/multi_coin_abnormal_volumes_tracker.py) | A strategy that scan a list of pairs in order to find abnormal volume increase. For each listed coins, the strategy will compute a moving average of the last candles volume to compare it with a bigger segment of candles.                                                                                                                                                   |
| [trend_follow](https://github.com/AntoineLep/ftx_algotrading/blob/main/strategies/trend_follow/trend_follow.py)                                                                     | A strategy that follow a coin trend by going long when a coin price is going up, and going short when the price is going down                                                                                                                                                                                                                                                  |
| [best_strat_ever](https://github.com/AntoineLep/ftx_algotrading/blob/main/strategies/best_strat_ever/best_strategy_ever.py)                                                         | A basic strategy for testing purposes                                                                                                                                                                                                                                                                                                                                          |
| [demo_strategy](https://github.com/AntoineLep/ftx_algotrading/blob/main/strategies/demo_strategy/demo_strategy.py)                                                                  | A basic strategy for demo purposes                                                                                                                                                                                                                                                                                                                                             |

### Create your own

Feel free to create your own strategy in the strategy folder or reuse the existing ones. You can use FTX API examples to
send trading orders. See [FTX official documentation](https://docs.ftx.com/).

## Disclaimer

I'm not responsible for any money losses using this bot and guarantee that it will not do anything else that what you
ask him to do in your strategies. Existing strategies can be used at your own risk, please have a deep look at the code
before running it.

## Credits

If you like this tool or if you're making too much money out of it, don't hesitate to give your feedback. You can share
some of your profit at my Ethereum address as well: `0xb27daa27010fc68A69b6361CCAECCE14aBEea4A8`

Issues and PR are welcome

Enjoy !