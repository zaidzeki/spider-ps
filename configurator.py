import ujson

with open("./config.json") as fp:
    config = ujson.load(fp)

ROOT = config["ROOT"]
MoodleSession = config["MoodleSession"]
sesskey = config["sesskey"]
client_id = config["client_id"]
itemid = config["itemid"]
verbose = config["verbose"]
CHUNK = config["chunk"]
MAX_RETRIES = config["max_retries"]
BUFFER_SIZE = 512 * 1024
