# ftx_algotrading
Simple algorithmic trading strategy runner for FTX

## Configure
Open `config/` folder and fill the private directory with a new file called `ftx_config.py` with your ftx api key info.
A template is given in this directory with some basic config info about ftx exchange and how to structure the
configuration file.

Also don't forget to fill the `application_config.py` file with the main strategy you want to run.

## Trading
This project comes with two built-in strategies:
* **best_strategy_ever:** A basic strategy for testing purposes
* **twitter_elon_musk_doge_tracker:** A strategy to automates DOGE-PERP position opening when Elon Musk tweets some Doge
  related content. It has some internal configuration using globals to set up position open and close conditions.
  This strategy has an internal `config/private/twitter_config.py` file  that has to be created before being able to run
  it. As for `ftx_config.py`, it comes with a template.


Feel free to create your own strategy in the strategy folder or reuse the existing ones.

You can use ftx api examples to send trading orders. See [FTX official documentation](https://docs.ftx.com/)

I'm not responsible for any money losses using this bot and guarantee that it will not do anything else that what you
ask him to do in your strategy.

If you're making too much money out of this trading bot and feel like you have to give me back some love,
do not hesitate to give you feedback or to share some of your profit at my eth address: 
`0xb27daa27010fc68A69b6361CCAECCE14aBEea4A8`

Enjoy !