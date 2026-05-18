from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import os
from datetime import datetime

INFLUXDB_URL = "http://influxdb:8086"
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET")

#create a single client instance to be reused across requests
client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG   
)

write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

def write_benchmark(model_name: str, metric: str, value: float):
    "Write a single benchmark data point to InfluxDB"
    point = (
        Point("benchmark")
        .tag("model", model_name)
        .tag("metric", metric)
        .field("value", value)
        .time(datetime.utcnow(), WritePrecision.NS)
    )
    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

def query_benchmarks(model_name: str, metric: str, hours: int = 1):
    "Query recent benchmark scores for a model"
    query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -{hours}h)
            |> filter(fn: (r) => r._measurement == "benchmark")
            |> filter(fn: (r) => r.model_name == "{model_name}")
            |> filter(fn: (r) => r.metric == "{metric}")
            |> sort(columns: ["_time"], desc: true)
    '''
    tables = query_api.query(query)
    results = []
    for table in tables:
        for record in table.records:
            results.append({
                "time": record.get_time(),
                "model_name": record["model_name"],
                "metric": record["metric"],
                "value": record.get_value()
            })
    return results

def query_latest_scores():
    "Get the most recent score per model per metric - for the leaderboard"
    query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "benchmark")
            |> group(columns: ["model_name", "metric"])
            |> last()
    '''
    tables = query_api.query(query)
    results = []
    for table in tables:
        for record in table.records:
            results.append({
                "time": record.get_time(),
                "model_name": record["model_name"],
                "metric": record["metric"],
                "value": record.get_value()
            })
    return results
