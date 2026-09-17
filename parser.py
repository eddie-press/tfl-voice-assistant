import re

LINE_ALIASES = {
    "northern": "northern",
    "piccadilly": "piccadilly",
    "central": "central",
    "victoria": "victoria",
    "jubilee": "jubilee",
    "district": "district",
    "circle": "circle",
    "bakerloo": "bakerloo",
    "metropolitan": "metropolitan",
    "hammersmith & city": "hammersmith-city",
    "hammersmith and city": "hammersmith-city",
    "waterloo & city": "waterloo-city",
    "waterloo and city": "waterloo-city",
    "elizabeth": "elizabeth",
    "elizabeth line": "elizabeth",
}

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

STATION_ALIASES = {
    "waterloo": "Waterloo",
    "waterloo station": "Waterloo",
    "kings cross": "King's Cross",
    "king's cross": "King's Cross",
    "kings cross station": "King's Cross",
    "st pancras": "St Pancras",
    "st pancras station": "St Pancras",
    "liverpool street": "Liverpool Street",
    "liverpool street station": "Liverpool Street",
    "paddington": "Paddington",
    "paddington station": "Paddington",
    "victoria": "Victoria",
    "victoria station": "Victoria",
    "bank": "Bank",
    "bank station": "Bank",
    "oxford circus": "Oxford Circus",
    "oxford circus station": "Oxford Circus",
    "leicester square": "Leicester Square",
    "leicester square station": "Leicester Square",
    "piccadilly circus": "Piccadilly Circus",
    "piccadilly circus station": "Piccadilly Circus",
    "green park": "Green Park",
    "green park station": "Green Park",
    "bond street": "Bond Street",
    "bond street station": "Bond Street",
    "stratford": "Stratford",
    "stratford station": "Stratford",
    "canary wharf": "Canary Wharf",
    "canary wharf station": "Canary Wharf",
    "holborn": "Holborn",
    "holborn station": "Holborn",
    "embankment": "Embankment",
    "embankment station": "Embankment",
    "blackfriars": "Blackfriars",
    "blackfriars station": "Blackfriars",
    "farringdon": "Farringdon",
    "farringdon station": "Farringdon",
    "tower hill": "Tower Hill",
    "tower hill station": "Tower Hill",
    "old street": "Old Street",
    "old street station": "Old Street",
    "euston": "Euston",
    "euston station": "Euston",
    "marylebone": "Marylebone",
    "marylebone station": "Marylebone",
    "baker street": "Baker Street",
    "baker street station": "Baker Street",
    "westminster": "Westminster",
    "westminster station": "Westminster",
    "south kensington": "South Kensington",
    "south kensington station": "South Kensington",
    "earls court": "Earl's Court",
    "earl's court": "Earl's Court",
    "earls court station": "Earl's Court",
    "notting hill gate": "Notting Hill Gate",
    "notting hill gate station": "Notting Hill Gate",
    "shepherds bush": "Shepherd's Bush",
    "shepherd's bush station": "Shepherd's Bush",
}

def clean(text):
    text = text.lower().replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip().rstrip("?!., ")

def find_line(text):
    for name, line_id in sorted(LINE_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(rf"\b{re.escape(name)}(?:\s+line)?\b", text):
            return line_id
    return None

def find_count(text):
    match = re.search(r"\b(\d+)\b", text)
    if match:
        return int(match.group(1))
    for word, number in NUMBER_WORDS.items():
        if re.search(rf"\b{word}\b", text):
            return number
    return 1

def is_status_intent(text):
    return any(x in text for x in [
        "delay", "delays", "delayed", "disruption", "disruptions",
        "problem", "problems", "issue", "issues",
        "running normally", "running normal", "running ok",
        "running okay", "working normally", "service status",
        "what's happening", "what is happening", "anything wrong"
    ])

def is_arrival_intent(text):
    return any(x in text for x in [
        "next", "coming", "arrive", "arrives", "arrival",
        "arrivals", "how long", "waiting", "wait"
    ])

def is_train_request(text):
    return any(x in text for x in ["train", "trains", "tube", "underground"])

def find_station(text):
    match = re.search(r"\b(?:at|from|into)\s+(?:the\s+)?(.+)$", text)
    if not match:
        return None

    station = match.group(1).strip(" ,.")
    station = re.sub(r"\s+(?:please|now|thanks|thank you)$", "", station).strip()
    station = re.sub(r"\s+(?:station|underground)$", "", station).strip()

    if station in STATION_ALIASES:
        return STATION_ALIASES[station]

    return station.title()

def parse_command(text):
    q = clean(text)
    line = find_line(q)

    if is_status_intent(q):
        if line:
            return {"intent": "line_status", "mode": "tube", "line": line}
        return {"intent": "network_status", "mode": "tube"}

    if line and is_arrival_intent(q):
        return {
            "intent": "line_arrivals",
            "mode": "tube",
            "line": line,
            "count": find_count(q)
        }

    if is_train_request(q) and is_arrival_intent(q):
        station = find_station(q)
        if station:
            return {
                "intent": "station_arrivals",
                "mode": "tube",
                "station": station,
                "count": find_count(q)
            }

    return {"intent": "unknown", "raw": text}
