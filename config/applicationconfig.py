from strategies.beststratever import BestStratEver
from strategies.twitter_elon_musk_doge_tracker.twitter_elon_musk_doge_tracker import TwitterElonMuskDogeTracker


name = "ftx_algotrading"
version = "1.0"
strategy = TwitterElonMuskDogeTracker()

log = {
    "level": "debug",
    "path": "logs"
}
