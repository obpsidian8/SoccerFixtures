from flask import Flask, request
from Scraper import SoccerScoresScraper, League
from HelperFunctions.SeleniumPageNavigator import SelemiumPageNavigetor, get_chrome_driver

app = Flask(__name__)

@app.route("/getleaguefixtures/premierleague", methods =["GET"])
def get_premierleague_fixtures():
    chrome_driver = get_chrome_driver(dataDirName="SoccerMatchesScraper")
    navigator = SelemiumPageNavigetor(chrome_driver)

    hide_scores= request.args.get("hide_scores")
    if not hide_scores or hide_scores == "false":
        hide_scores=False
    else:
        hide_scores = True

    scraper = SoccerScoresScraper(navigator, league=League.PERMIER_LEAGUE)
    scraper.get_results_page()
    scraper.enter_search_term()
    all_fixtures_and_links = scraper.get_current_match_day_data(hide_scores=hide_scores)

    return all_fixtures_and_links

@app.route("/getleaguefixtures/bundesliga")
def get_bundesliga_fixtures():
    chrome_driver = get_chrome_driver(dataDirName="SoccerMatchesScraper")
    navigator = SelemiumPageNavigetor(chrome_driver)

    scraper = SoccerScoresScraper(navigator, league=League.BUNDESLIGA)
    scraper.get_results_page()
    scraper.enter_search_term()
    all_fixtures_and_links = scraper.get_current_match_day_data(hide_scores=False)

    return all_fixtures_and_links

@app.route("/")
def index():
    return "Hello"

if __name__ == "__main__":
    app.run(debug=True)
