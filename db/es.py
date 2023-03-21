from elasticsearch import Elasticsearch

host = "http://172.26.164.93:19201"
username = "elastic"
password = "SitMid2022!!"
es = Elasticsearch(
    host,
    http_auth=(username, password),
    headers={"Content-Type": "application/json; charset=UTF-8"}
)
