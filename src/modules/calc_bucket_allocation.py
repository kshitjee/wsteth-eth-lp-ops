import math
from src.modules.get_metrics import MetricsCollector

class BucketAllocator:
    def __init__(self, 
                 volatility_threshold=0.01, 
                 narrow_pct=0.001,    # ±0.1% narrow range
                 wide_pct=0.002):     # ±0.2% wide range
        self.volatility_threshold = volatility_threshold
        self.narrow_pct = narrow_pct
        self.wide_pct = wide_pct

    def _offset_in_ticks(self, pct):
        return int(math.log(1 + pct, 1.0001))

    def calculate_buckets(self, tick, volatility):
        if volatility < self.volatility_threshold:
            narrow_alloc = 0.9
            wide_alloc = 0.1
        else:
            narrow_alloc = 0.6
            wide_alloc = 0.4

        narrow_offset = self._offset_in_ticks(self.narrow_pct)
        wide_offset = self._offset_in_ticks(self.wide_pct)

        narrow_bucket = (tick - narrow_offset, tick + narrow_offset)
        wide_bucket = (tick - wide_offset, tick + wide_offset)

        return {
            "narrow_bucket": narrow_bucket,
            "wide_bucket": wide_bucket,
            "narrow_allocation": narrow_alloc,
            "wide_allocation": wide_alloc
        }

    @staticmethod
    def get_current_metrics(api_key, subgraph_id, pool_id):
        collector = MetricsCollector(api_key, subgraph_id, pool_id)
        metrics = collector.get_metrics()
        pool_data = metrics.get("pool_data", {})
        tick = int(pool_data.get("tick", 0))
        sqrt_price = int(pool_data.get("sqrtPrice", 0))
        volatility = metrics.get("daily_volatility", 0.0)
        price = (sqrt_price / (2**96)) ** 2
        return {"tick": tick, "volatility": volatility, "price": price}

    @staticmethod
    def get_current_bucket_allocation(api_key, subgraph_id, pool_id, 
                                      volatility_threshold=0.01, 
                                      narrow_pct=0.001, 
                                      wide_pct=0.002):
        current = BucketAllocator.get_current_metrics(api_key, subgraph_id, pool_id)
        tick = current["tick"]
        volatility = current["volatility"]
        price = current["price"]

        allocator = BucketAllocator(volatility_threshold, narrow_pct, wide_pct)
        buckets = allocator.calculate_buckets(tick, volatility)
        return {
            "current_tick": tick,
            "current_price": price,
            "daily_volatility": volatility,
            "allocation": buckets
        }

if __name__ == "__main__":
    API_KEY = "6bfcf592f7ffd72bce3c7e77bad7f5e5"
    SUBGRAPH_ID = "5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
    POOL_ID = "0xd340b57aacdd10f96fc1cf10e15921936f41e29c"

    current_allocation = BucketAllocator.get_current_bucket_allocation(
        API_KEY, SUBGRAPH_ID, POOL_ID,
        volatility_threshold=0.01,
        narrow_pct=0.001,
        wide_pct=0.002
    )
    print("Current Bucket Allocation:")
    print(current_allocation)