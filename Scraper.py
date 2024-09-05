from SeleniumPageNavigator import SelemiumPageNavigetor, get_chrome_driver
from LoggingModule import set_logging
from enum import Enum
import json
import re

logger = set_logging(__name__)


class League(Enum):
    PERMIER_LEAGUE = "Premier League matches"
    LA_LIGA = "La liga matches"
    BUNDESLIGA = "Bundesliga matches"
    SERIEA = "Serie A matches"
    CHAMPIONS_LEAGUE = "Champions League matches"


class SoccerScoresScraper:
    SEARCH_URL = "https://www.google.com/"

    def __init__(self, navigator: SelemiumPageNavigetor, league: League) -> None:
        self.navigator = navigator
        self.league = league

    def get_results_page(self):
        self.navigator.get_page(self.SEARCH_URL)

    def enter_search_term(self):
        search_box_xpath = "//textarea[@aria-label='Search']"
        enter_Search_term_try = self.navigator.enter_field_value(xpath=search_box_xpath, value=self.league.value)
        if not enter_Search_term_try:
            logger.info(f"Entering Search term \'{self.league.value}' was unsuccessfull")
            return

        self.navigator.sendReturnKey(xpath=search_box_xpath, time_delay=1)

        see_more_button_xpath = "//g-expandable-content[contains(@aria-hidden, 'false')]//*[contains(text(),'More matches')]"
        self.navigator.click_element(xpath=see_more_button_xpath)

    def get_current_match_day_data(self, hide_scores=False):
        all_match_day_xpath = "(//div[contains(@data-title, 'Matchday')])"

        num_match_days_displayed = self.navigator.get_number_of_elements(xpath=all_match_day_xpath,time_delay=1)
        logger.info(f"num_match_days_displayed for {self.league.name}: {num_match_days_displayed}")

        match_day_groups = {}

        for matchday_num in range(num_match_days_displayed):
            if matchday_num == 0:
                continue
            match_day_groups[f"Matchday{matchday_num}"] = []

            current_match_day_xpath = f"{all_match_day_xpath}[{matchday_num + 1}]/.."

            relative_match_list_summary_xpath = "//div[@data-entityname='Match List Summary']"

            current_match_list_summary_xpath = current_match_day_xpath + relative_match_list_summary_xpath

            match_fixture_xpath_relative = "//td[contains(@class, 'liveresults-sports-immersive')]"

            complete_match_fixture_xpath = f"({current_match_list_summary_xpath}{match_fixture_xpath_relative})"
            num_matches = self.navigator.get_number_of_elements(xpath=complete_match_fixture_xpath, time_delay=1)
            logger.info(f"Number of matches for matchday {matchday_num}: {num_matches}")

            for fixture_num in range(num_matches):
                current_fixture_xpath = f"({complete_match_fixture_xpath})[{fixture_num + 1}]"

                match_day_html = self.navigator.getHtmlElementObjectAsText(xpath=current_fixture_xpath)

                # match_day_html = match_day_html.replace("\n", "#")
                logger.info(f'Fixture text for index {fixture_num} in matchday {matchday_num}: {match_day_html}\n')
                if not match_day_html or 'class="liveresults-sports-immersive__empty-tile' in  match_day_html:
                    continue

                teams_and_scores_regex = re.compile(r'class="imspo_mt__tt-w">(.+?)<[\s\S]*?data-df-team-mid[\s\S]*?aria-hidden="true">(.+?)<')
                teams_and_scores_search_results = teams_and_scores_regex.findall(match_day_html)

                if matchday_num > 0:
                    if not teams_and_scores_search_results: #For upcoming matches with no scores yet
                        teams_and_scores_regex = re.compile(r'><div class="liveresults-sports-immersive__hide-element">(.+?)<')
                        teams_and_scores_search_results  = teams_and_scores_regex.findall(match_day_html)
                        teams_and_scores_search_results[0] = ("upcoming", teams_and_scores_search_results[0])
                        teams_and_scores_search_results[1] = ("upcoming", teams_and_scores_search_results[1])

                logger.info(f"teams_and_scores_search_results for fixture index {fixture_num} in matchday {matchday_num}: {teams_and_scores_search_results}")

                if len(teams_and_scores_search_results) < 1:
                    # Process upcoming match fixture
                    continue

                date_regex = re.compile(r'match-status[\s\S]*?imspo_mt[\s\S]*?aria-label.+?">(.+?)<')
                date_search_results = date_regex.findall(match_day_html)
                if not date_search_results:
                    date_regex = re.compile(r'imspo_mt__date">(.+?)<')
                    date_search_results = date_regex.findall(match_day_html)
                    if not date_search_results:
                        continue

                # match_day_html = self.navigator.getHtmlElementObjectAsText(xpath=current_fixture_xpath)
                youtube_link_regex = re.compile(r'(https:\/\/www\.youtube\.com\/watch\?v=.+?)&')
                youtube_thumbnail_regex = re.compile(r'https:\/\/www\.youtube\.com\/watch\?v=.+?&[\s\S]*?img\s+class.+?src="(.+?)"')

                youtube_link_search_results = youtube_link_regex.findall(match_day_html)
                logger.info(f"Youtube Links: {youtube_link_search_results}")

                youtube_thumbnail_search_results = youtube_thumbnail_regex.findall(match_day_html)
                logger.info(f"Youtube Thumbnail: {youtube_thumbnail_search_results}")

                fixture_json_results = {}
                fixture_json_results["Teams"] = {}

                fixture_json_results["FixtureNum"] = f"FixtureNum{fixture_num+1}"
                if hide_scores and teams_and_scores_search_results[0][0] != "upcoming":
                    fixture_json_results["Teams"][teams_and_scores_search_results[0][1]] = "**"
                    fixture_json_results["Teams"][teams_and_scores_search_results[1][1]] = "**"
                else:
                    fixture_json_results["Teams"][teams_and_scores_search_results[0][1]] = teams_and_scores_search_results[0][0]
                    fixture_json_results["Teams"][teams_and_scores_search_results[1][1]] = teams_and_scores_search_results[1][0]

                if youtube_link_search_results:
                    fixture_json_results["Highlights"] = youtube_link_search_results[0]
                else:
                    fixture_json_results["Highlights"] = "No Highlights for match"

                if youtube_thumbnail_search_results:
                    fixture_json_results["Video Thumbnail"] = f"https:{youtube_thumbnail_search_results[0]}"
                else:
                    fixture_json_results["Video Thumbnail"] = "N/A"

                fixture_json_results["Date"] = date_search_results[0]
                logger.info(f"fixture_json_results:{json.dumps(fixture_json_results, indent=2)}\n")
                match_day_groups[f"Matchday{matchday_num}"].append(fixture_json_results)

            if not match_day_groups[f"Matchday{matchday_num}"]:
                match_day_groups.pop(f"Matchday{matchday_num}")



        logger.info(f"All match fixtures: {json.dumps(match_day_groups, indent=2)}")
        logger.info("Got all current fixtures")

        file_name = f'{self.league.value.replace(" ", "_")}.json'
        with open(file_name, "w") as f:
            json.dump(match_day_groups, f)

        return match_day_groups


def run_scraper():
    chrome_driver = get_chrome_driver(dataDirName="SoccerMatchesScraper", headless=False)
    navigator = SelemiumPageNavigetor(chrome_driver)

    scraper = SoccerScoresScraper(navigator, league=League.BUNDESLIGA)
    scraper.get_results_page()
    scraper.enter_search_term()
    all_fixtures_and_links = scraper.get_current_match_day_data(hide_scores=True)

    logger.info("done")

    return all_fixtures_and_links


if __name__ == "__main__":
    run_scraper()
