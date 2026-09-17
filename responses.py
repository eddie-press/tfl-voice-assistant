def minutes(seconds):
    return max(0, round(seconds / 60))

def format_result(result):
    if result["type"] == "error":
        return result["message"]

    if result["type"] == "line_status":
        statuses = []

        for item in result["data"]:
            for status in item.get("lineStatuses", []):
                statuses.append(
                    status.get("statusSeverityDescription", "Unknown")
                )

        status = statuses[0] if statuses else "Unknown"
        return f"The {result['line'].title()} line is currently: {status}."

    if result["type"] == "line_arrivals":
        if not result["data"]:
            return f"No live {result['line'].title()} line arrivals were returned."

        rows = [
            f"{minutes(item.get('timeToStation', 0))} min — "
            f"{item.get('destinationName', 'Unknown destination')}"
            for item in result["data"]
        ]

        return (
            f"Next {len(rows)} {result['line'].title()} line trains:\n"
            + "\n".join(rows)
        )

    if result["type"] == "station_arrivals":
        if not result["data"]:
            return (
                f"No live Underground arrivals were returned "
                f"for {result['station']}."
            )

        rows = [
            f"{minutes(item.get('timeToStation', 0))} min — "
            f"{item.get('lineName', 'Unknown')} towards "
            f"{item.get('destinationName', 'Unknown destination')}"
            for item in result["data"]
        ]

        return (
            f"Next {len(rows)} Underground arrivals at "
            f"{result['station']}:\n"
            + "\n".join(rows)
        )

    return "No result."
