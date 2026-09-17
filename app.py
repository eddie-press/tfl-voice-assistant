from flask import Flask, render_template, request
from parser import parse_command
from tfl_api import TfLClient
from responses import format_result

app = Flask(__name__)
tfl = TfLClient()

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    command = None
    raw = ""

    if request.method == "POST":
        raw = request.form.get("command", "").strip()
        if raw:
            command = parse_command(raw)
            try:
                result = format_result(tfl.execute(command))
            except Exception as error:
                result = "Sorry, I couldn't retrieve the TfL data. Please try again."
                print("ERROR:", error)

    return render_template("index.html", result=result, command=command, raw=raw)

if __name__ == "__main__":
    app.run(debug=True)
