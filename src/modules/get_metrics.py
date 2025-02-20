import requests
import math
import statistics

class MetricsCollector:
    def __init__(self, api_key, subgraph_id, pool_id):
        self.api_key = api_key
        self.subgraph_id = subgraph_id
        self.pool_id = pool_id
        self.endpoint = f"https://gateway.thegraph.com/api/{api_key}/subgraphs/id/{subgraph_id}"

    def _query_subgraph(self, query):
        response = requests.post(self.endpoint, json={'query': query})
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Query failed with status code {response.status_code}")

    def get_pool_data(self):
        query = f'''
        {{
          pool(id: "{self.pool_id}") {{
            tick
            sqrtPrice
            liquidity
            volumeUSD
          }}
        }}
        '''
        return self._query_subgraph(query)

    def get_pool_day_data(self):
        query = f'''
        {{
          poolDayDatas(first: 1, orderBy: date, orderDirection: desc, where: {{pool: "{self.pool_id}"}}) {{
            date
            liquidity
            sqrtPrice
            volumeToken0
            volumeToken1
          }}
        }}
        '''
        return self._query_subgraph(query)

    def get_historical_pool_day_data(self, days=7):
        # Fetch the last 'days' entries
        query = f'''
        {{
          poolDayDatas(first: {days}, orderBy: date, orderDirection: desc, where: {{pool: "{self.pool_id}"}}) {{
            date
            sqrtPrice
            volumeToken0
            volumeToken1
          }}
        }}
        '''
        return self._query_subgraph(query)

    def compute_24h_volume(self):
        data = self.get_pool_day_data()
        entries = data.get("data", {}).get("poolDayDatas", [])
        if entries:
            latest = entries[0]
            return {
                "date": latest["date"],
                "volumeToken0": latest["volumeToken0"],
                "volumeToken1": latest["volumeToken1"]
            }
        return {}

    def compute_daily_volatility(self, days=7):
        data = self.get_historical_pool_day_data(days)
        entries = data.get("data", {}).get("poolDayDatas", [])
        if len(entries) < 2:
            return 0.0

        prices = []
        # Convert sqrtPrice (Q64.96) to actual price: (sqrtPrice / 2**96)^2
        for entry in entries:
            sqrt_price = int(entry["sqrtPrice"])
            price = (sqrt_price / (2**96)) ** 2
            prices.append(price)
        # Compute daily log returns
        returns = [math.log(prices[i] / prices[i+1]) for i in range(len(prices) - 1)]
        return statistics.stdev(returns) if returns else 0.0

    def get_metrics(self):
        pool_data = self.get_pool_data()
        pool_day_data = self.get_pool_day_data()
        volume_24h = self.compute_24h_volume()
        volatility = self.compute_daily_volatility()
        return {
            "pool_data": pool_data.get("data", {}).get("pool", {}),
            "pool_day_data": pool_day_data.get("data", {}).get("poolDayDatas", []),
            "24h_volume": volume_24h,
            "daily_volatility": volatility
        }

if __name__ == "__main__":
    API_KEY = "6bfcf592f7ffd72bce3c7e77bad7f5e5"
    SUBGRAPH_ID = "5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV"
    POOL_ID = "0xd340b57aacdd10f96fc1cf10e15921936f41e29c"

    collector = MetricsCollector(API_KEY, SUBGRAPH_ID, POOL_ID)
    metrics = collector.get_metrics()
    print(metrics)