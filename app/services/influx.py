from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import os
from datetime import datetime

INFLUXDB_URL = "http://influxdb:8086"
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN") or ""
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG") or ""
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET") or ""

#helper function to serialize influxdb records, converting datetime objects to ISO format strings for JSON serialization
def serialize_record(records: list[dict]) -> list[dict]:
    serialized = []
    for record in records:
        serialized_record = {}
        for key, value in record.items():
            if isinstance(value, datetime):
                serialized_record[key] = value.isoformat()
            else:
                serialized_record[key] = value
        serialized.append(serialized_record)
    return serialized


#create a single client instance to be reused across requests
client = InfluxDBClient(
    url=INFLUXDB_URL,
    token=INFLUXDB_TOKEN,
    org=INFLUXDB_ORG   
)

write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

def write_benchmark(model_name: str, metric: str, value: float, category: str, judge: str):
    "Write a single benchmark data point to InfluxDB"
    point = (
        Point("benchmark")  #Point is a data structure representing a single measurement in InfluxDB, with a measurement name of "benchmark"
        .tag("model_name", model_name)  #tag is a key-value pair used for indexing and querying in InfluxDB, here we add a tag for the model name
        .tag("metric", metric)  
        .tag("judge",judge)
        .tag("category", category)
        .field("value", float(value))  #field is the actual data value we want to store, here we add a field for the metric value
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

def query_latest_scores(category: str, judge: str, metric: str = "accuracy"):  #powers the leaderboard
    "Get the most recent score per model per metric - for the leaderboard"
    query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -24h)
            |> filter(fn: (r) => r._measurement == "benchmark")
            |> filter(fn: (r) => r.category == "{category}")
            |> filter(fn: (r) => r.judge == "{judge}")
            |> filter(fn: (r) => r.metric == "{metric}")
            |> group(columns: ["model_name"])
            |> last()
        '''
    tables = query_api.query(query)
    results = []
    print(f"DEBUG: tables = {tables}")
    for table in tables:
        for record in table.records:
            results.append({
                "time": record.get_time().isoformat(),  #convert datetime to ISO string for JSON serialization
                "model_name": record["model_name"],
                "metric": record["metric"],
                "value": record.get_value()
            })
    print(f"DEBUG: results = {results}")
    return results
