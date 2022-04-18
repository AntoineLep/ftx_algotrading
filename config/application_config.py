from strategies.trend_follow.trend_follow import TrendFollow
from strategies.twitter_elon_musk_doge_tracker.twitter_elon_musk_doge_tracker import TwitterElonMuskDogeTracker
from strategies.best_strat_ever.best_strategy_ever import BestStrategyEver
from strategies.listing_sniper.listing_sniper import ListingSniper
from strategies.multi_coin_abnormal_volumes_tracker.multi_coin_abnormal_volumes_tracker \
    import MultiCoinAbnormalVolumeTracker

strategy = MultiCoinAbnormalVolumeTracker()

log = {
    "level": "info",
    "path": "logs"
}
