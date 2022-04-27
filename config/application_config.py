from strategies.demo_strategy.demo_strategy import DemoStrategy
from strategies.cryptofeed_strategy.cryptofeed_strategy import CryptofeedStrategy
from strategies.trend_follow.trend_follow import TrendFollow
from strategies.twitter_elon_musk_doge_tracker.twitter_elon_musk_doge_tracker import TwitterElonMuskDogeTracker
from strategies.best_strat_ever.best_strategy_ever import BestStrategyEver
from strategies.listing_sniper.listing_sniper import ListingSniper
from strategies.multi_coin_abnormal_volume_tracker.multi_coin_abnormal_volume_tracker \
    import MultiCoinAbnormalVolumeTracker

strategy = CryptofeedStrategy()

log = {
    "level": "info",
    "path": "logs"
}
