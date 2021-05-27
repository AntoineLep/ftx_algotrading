# ftx_algotrading

Simple algorithmic trading strategy runner for FTX

## Configure

Open `config/` folder and fill the private directory with a new file called `ftx_config.py` with your ftx api key info.
A template is given in this directory with some basic config info about ftx exchange and how to structure the
configuration file.

Also don't forget to fill the `application_config.py` file with the main strategy you want to run.

## Trading strategies

This project comes with two built-in strategies:

### best_strategy_ever

A basic strategy for testing purposes

### twitter_elon_musk_doge_tracker

A strategy to automates DOGE-PERP position opening when Elon Musk tweets some Doge related content.

It has some internal configuration using globals to set up position open and close conditions. This strategy has an
internal `config/private/twitter_config.py` file that has to be created before being able to run it. As
for `ftx_config.py`, it comes with a template.

> :warning: Make sure to use x20 leverage on your sub account before using this strategy (account > settings > margin)

### Create your own

Feel free to create your own strategy in the strategy folder or reuse the existing ones. You can use ftx api examples to
send trading orders. See [FTX official documentation](https://docs.ftx.com/).

You can use the PositionDriver class as well to run position with more ease.
It allows to create simple position opening setup with trigger orders for taking profit or stopping losses.


![image](https://user-images.githubusercontent.com/6230724/119690499-0a9f4700-be4a-11eb-92f7-7259a13eedc2.png)

## Disclaimer

I'm not responsible for any money losses using this bot and guarantee that it will not do anything else that what you
ask him to do in your strategy. Existing strategies can be used at your own risk, please have a close look at the code
before running it.

## Credits

If you're making too much money out of this trading bot and feel like you have to give me back some love, do not
hesitate to give your feedback or to share some of your profit at my ETH address:
`0xb27daa27010fc68A69b6361CCAECCE14aBEea4A8`

Issues and PR are welcomed

Enjoy !