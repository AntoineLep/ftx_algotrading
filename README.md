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


## Get started

Open `config/` folder and fill the `private/` directory with a new file called `ftx_config.py` with your ftx api key
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
from strategies.best_strat_ever.best_strategy_ever import BestStrategyEver

strategy = BestStrategyEver()

log = {
    "level": "info",
    "path": "logs"
}
```

## Trading strategies

### twitter_elon_musk_doge_tracker

A strategy to automates DOGE-PERP position opening when Elon Musk tweets some Doge related content.

It has some internal configuration using globals to set up position open and close conditions. This strategy has an
internal `config/private/twitter_config.py` file that has to be created before being able to run it. As
for `ftx_config.py`, it comes with a template.

> :warning: Make sure to use x20 leverage on your sub account before using this strategy (account > settings > margin)

### listing_sniper

A strategy to snipe a given pair listing.
It has some internal configuration using globals to configure which amount to invest and to set up the market pair to 
snipe

### multi coin abnormal volume tracker

A strategy that scan a list of pairs in order to find abnormal volume increase.
For each listed coins, the strategy will compute a moving average of the last candles volume to compare it with a
bigger segment of candles.

It has some internal configuration using globals to configure volume check (factor, short ma, long ma), price variation,
open and close conditions, and some other stuff documented inside strategy file.

### best_strategy_ever

A basic strategy for testing purposes

### Create your own

Feel free to create your own strategy in the strategy folder or reuse the existing ones. You can use ftx api examples to
send trading orders. See [FTX official documentation](https://docs.ftx.com/).

You can use the PositionDriver class as well to run position with more ease. It allows creating simple position opening
setup with trigger orders for taking profit or stopping losses.

![image](https://user-images.githubusercontent.com/6230724/119690499-0a9f4700-be4a-11eb-92f7-7259a13eedc2.png)

## Disclaimer

I'm not responsible for any money losses using this bot and guarantee that it will not do anything else that what you
ask him to do in your strategy. Existing strategies can be used at your own risk, please have a close look at the code
before running it.

## Credits

If you're making too much money out of this trading bot and feel like you have to give me back some love, do not
hesitate to give your feedback or to share some of your profit at my ETH address:
`0xb27daa27010fc68A69b6361CCAECCE14aBEea4A8`

Issues and PR are welcome

Enjoy !