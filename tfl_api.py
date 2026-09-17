
import os
import requests
from urllib.parse import quote


BASE_URL = "https://api.tfl.gov.uk"


TUBE_LINES = (
    "bakerloo,"
    "central,"
    "circle,"
    "district,"
    "hammersmith-city,"
    "jubilee,"
    "metropolitan,"
    "northern,"
    "piccadilly,"
    "victoria,"
    "waterloo-city,"
    "elizabeth"
)


# Reliable station IDs for the main London stations.
# These are TfL NaPTAN station IDs.

STATION_IDS = {
    "waterloo": "940GZZLUWLO",
    "kings cross": "940GZZLUKSX",
    "king's cross": "940GZZLUKSX",
    "st pancras": "940GZZLUSKP",
    "liverpool street": "940GZZLULST",
    "paddington": "940GZZLUPAC",
    "victoria": "940GZZLUVIC",
    "bank": "940GZZLUBNK",
    "oxford circus": "940GZZLUOXC",
    "leicester square": "940GZZLULSQ",
    "piccadilly circus": "940GZZLUPCC",
    "green park": "940GZZLUGPK",
    "bond street": "940GZZLUBND",
    "stratford": "940GZZLUSTD",
    "canary wharf": "940GZZLUCAW",
    "holborn": "940GZZLUHBN",
    "embankment": "940GZZLUEMB",
    "blackfriars": "940GZZLUBFR",
    "farringdon": "940GZZLUFPK",
    "tower hill": "940GZZLUTWH",
    "old street": "940GZZLUODS",
    "euston": "940GZZLUEUS",
    "marylebone": "940GZZLUMYB",
    "baker street": "940GZZLUBST",
    "westminster": "940GZZLUWSM",
    "south kensington": "940GZZLUSKS",
    "earls court": "940GZZLUECT",
    "earl's court": "940GZZLUECT",
    "notting hill gate": "940GZZLUNHG",
    "shepherds bush": "940GZZLUSBC",
}


class TfLClient:

    def __init__(self):

        self.app_key = os.getenv(
            "TFL_APP_KEY",
            ""
        )

        self.session = requests.Session()

    # ---------------------------------------------------------
    # Basic API request
    # ---------------------------------------------------------

    def get(self, path, params=None):

        params = dict(params or {})

        if self.app_key:
            params["app_key"] = self.app_key

        url = BASE_URL + path

        response = self.session.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    # ---------------------------------------------------------
    # Main command executor
    # ---------------------------------------------------------

    def execute(self, command):

        intent = command.get("intent")

        if intent == "line_status":

            return self.get_line_status(
                command["line"]
            )

        if intent == "line_arrivals":

            return self.get_line_arrivals(
                command["line"],
                command["count"]
            )

        if intent == "station_arrivals":

            return self.get_station_arrivals(
                command["station"],
                command["count"]
            )

        if intent == "network_status":

            return {
                "type": "error",
                "message": (
                    "Please specify a Tube line, "
                    "such as Northern or Piccadilly."
                )
            }

        return {
            "type": "error",
            "message": (
                "I don't recognise that request yet."
            )
        }

    # ---------------------------------------------------------
    # Line status
    # ---------------------------------------------------------

    def get_line_status(self, line):

        data = self.get(
            f"/Line/{line}/Status"
        )

        return {
            "type": "line_status",
            "line": line,
            "data": data
        }

    # ---------------------------------------------------------
    # Arrivals for an entire line
    # ---------------------------------------------------------

    def get_line_arrivals(self, line, count):

        data = self.get(
            f"/Line/{line}/Arrivals"
        )

        if not isinstance(data, list):
            data = []

        data.sort(
            key=lambda item: item.get(
                "timeToStation",
                10**9
            )
        )

        return {
            "type": "line_arrivals",
            "line": line,
            "count": count,
            "data": data[:count]
        }

    # ---------------------------------------------------------
    # Arrivals at a station
    # ---------------------------------------------------------

    def get_station_arrivals(self, station, count):

        station_key = self.normalise_station(
            station
        )

        # First use our reliable station ID table.
        stop_id = STATION_IDS.get(
            station_key
        )

        # If it isn't in the table, ask TfL.
        if not stop_id:

            stop = self.search_stop(
                station
            )

            if not stop:

                return {
                    "type": "error",
                    "message": (
                        f"I couldn't find the London "
                        f"Underground station '{station}'."
                    )
                }

            stop_id = stop["id"]

        print(
            f"Station: {station}"
        )

        print(
            f"Stop ID: {stop_id}"
        )

        # IMPORTANT:
        #
        # Ask TfL directly for all Tube and Elizabeth
        # line predictions at this station.
        #
        # TfL explicitly supports:
        #
        # /Line/{ids}/Arrivals/{stopPointId}
        #
        # where {ids} can contain multiple comma-separated
        # line IDs.

        try:

            data = self.get(
                f"/Line/{TUBE_LINES}/Arrivals/{stop_id}"
            )

        except requests.RequestException as error:

            print(
                "Station arrival request failed:"
            )

            print(error)

            return {
                "type": "error",
                "message": (
                    "TfL could not return live arrival "
                    f"information for {station}."
                )
            }

        if not isinstance(data, list):
            data = []

        # Do not filter on modeName.
        #
        # TfL has already received a request specifically
        # for Tube/Elizabeth lines and this particular
        # station. Filtering the response again was causing
        # valid predictions to be discarded.

        data.sort(
            key=lambda item: item.get(
                "timeToStation",
                10**9
            )
        )

        print(
            f"Arrivals returned: {len(data)}"
        )

        return {
            "type": "station_arrivals",
            "station": station.title(),
            "count": count,
            "data": data[:count]
        }

    # ---------------------------------------------------------
    # Station search
    # ---------------------------------------------------------

    def search_stop(self, query):

        query = self.normalise_station(
            query
        )

        # Try the TfL search endpoint if we don't have
        # a known station ID.

        try:

            data = self.get(
                f"/StopPoint/Search/"
                f"{quote(query, safe='')}"
            )

        except requests.RequestException:

            return None

        matches = data.get(
            "matches",
            []
        )

        if not matches:
            return None

        # Prefer Tube/Elizabeth line stops.
        tube_matches = []

        for match in matches:

            modes = [
                str(mode).lower()
                for mode in match.get(
                    "modes",
                    []
                )
            ]

            if (
                "tube" in modes
                or "elizabeth-line" in modes
            ):
                tube_matches.append(
                    match
                )

        if not tube_matches:
            return None

        query_clean = self.normalise_station(
            query
        )

        # Exact match first.

        for match in tube_matches:

            name = self.normalise_station(
                match.get(
                    "name",
                    ""
                )
            )

            common_name = self.normalise_station(
                match.get(
                    "commonName",
                    ""
                )
            )

            if (
                name == query_clean
                or common_name == query_clean
            ):
                return match

        # Otherwise return the first Tube match.

        return tube_matches[0]

    # ---------------------------------------------------------
    # Station-name normalisation
    # ---------------------------------------------------------

    @staticmethod
    def normalise_station(name):

        name = str(
            name
        ).lower()

        name = name.replace(
            "’",
            "'"
        )

        name = name.strip()

        for suffix in (
            " underground station",
            " underground",
            " station",
            " stn"
        ):

            if name.endswith(suffix):

                name = name[
                    :-len(suffix)
                ]

                break

        name = " ".join(
            name.split()
        )

        return name
