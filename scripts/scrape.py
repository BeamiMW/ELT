from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import logging
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json

# set up logging
logging.basicConfig(level=logging.INFO)

# set Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument('--disable-headless')  # run in headless mode (no graphical interface)
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--window-size=1920,1080')  # set window size for headless browser
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('start-maximized')
chrome_options.add_argument('--remote-debugging-port=9222')

# disable images to speed up scraping
prefs = {'profile.managed_default_content_settings.images': 2}
chrome_options.add_experimental_option('prefs', prefs)

# set the path to chrome driver
chrome_driver_path = '/usr/bin/chromedriver'

# initialize the chrome web driver
driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)

try:
    logging.info('Opening IMDb page...')
    # access IMDb top indonesian movies page
    driver.get('https://www.imdb.com/list/ls062594700/')

    logging.info('Page loaded, waiting for elements...')
    # wait for the movie list elements to appear
    WebDriverWait(driver, 120).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.ipc-metadata-list li.ipc-metadata-list-summary-item'))
    )

    time.sleep(5)
    logging.info('Elements found, starting to scrape...')

    # grab all the <li> elements containing the movie list
    films = driver.find_elements(By.CSS_SELECTOR, 'ul.ipc-metadata-list li.ipc-metadata-list-summary-item')

    # list to store movie data
    data = []

    # loop through the movie list and extract relevant information
    for film in films:
        # extract movie title
        try:
            title = film.find_element(By.CSS_SELECTOR, 'div.ipc-title a.ipc-title-link-wrapper h3.ipc-title__text').text
        except Exception as e:
            logging.warning(f'Title not found: {e}')
            title = 'N/A' # if the title is not found

        # extract release year
        try:
            year = film.find_element(By.CSS_SELECTOR, 'span.sc-ab348ad5-8.cSWcJI.dli-title-metadata-item').text.strip('()')
        except Exception as e:
            logging.warning(f'Year not found: {e}')
            year = 'N/A'

        # extract runtime
        try:
            runtime = film.find_element(By.CSS_SELECTOR, 'span.sc-ab348ad5-8.cSWcJI.dli-title-metadata-item:nth-of-type(2)').text
        except Exception as e:
            logging.warning(f'Runtime not found: {e}')
            runtime = 'N/A'

        # extract rating
        try:
            rating = film.find_element(By.CSS_SELECTOR, 'span.ipc-rating-star--rating').text
        except Exception as e:
            logging.warning(f'Rating not found: {e}')
            rating = 'N/A'

        # extract voting count
        try:
            voting = film.find_element(By.CSS_SELECTOR, 'span.ipc-rating-star--voteCount').text
        except Exception as e:
            logging.warning(f"Voting count not found: {e}")
            voting = 'N/A'

        # extract metascore
        try:
            metascore = film.find_element(By.CSS_SELECTOR, 'span.sc-b0901df4-0.bXIOoL.metacritic-score-box').text
        except Exception as e:
            logging.warning(f"Metascore not found: {e}")
            metascore = 'N/A'

        # extract description (if available)
        try:
            description = film.find_element(By.CSS_SELECTOR, 'div.ipc-html-content-inner-div').text
        except Exception as e:
            logging.warning(f'Description not found: {e}')
            description = 'N/A'

        # extract director's name
        try:
            director = film.find_element(By.CSS_SELECTOR, 'a.ipc-link.ipc-link--base.dli-director-item').text
        except Exception as e:
            logging.warning(f'Director not found: {e}')
            director = 'N/A'

        # extract stars (actors)
        try:
            stars_elements = film.find_elements(By.CSS_SELECTOR, 'a.ipc-link.ipc-link--base.dli-cast-item')
            stars = ', '.join([star.text for star in stars_elements])  # Join actor names
        except Exception as e:
            logging.warning(f'Stars not found: {e}')
            stars = 'N/A'

        # save the extracted movie data
        film_data = {
            'Title': title,
            'Years': year,
            'Runtime': runtime,
            'Rating': rating,
            'Voting': voting,
            'Metascore': metascore,
            'Descriptions': description,
            'Director': director,
            'Stars': stars
        }

        # append to the data list
        data.append(film_data)

    # save the data into a JSON file
    json_path = '/opt/airflow/data/imdb_top_20_indonesia.json'
    with open(json_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    # load data from JSON into pandas dataframe
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)

    df = pd.DataFrame(data)

    # save the dataframe to CSV
    df.to_csv('/opt/airflow/data/imdb_top_20_indonesia.csv', index=False)

except TimeoutException:
    driver.save_screenshot('/data/scraping_error.png')
    raise

finally:
    driver.quit()
