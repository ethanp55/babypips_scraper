from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import numpy as np
import pandas as pd
import requests


event_data = []


def parse_response(resp):
    # Make sure the request was succesful
    if resp.status_code == 200:
        # Create a bs4 object
        html = resp.text
        html_soup = BeautifulSoup(html, 'html.parser')

        # Navigate down to the actual event data
        body = html_soup.find('body', class_='cardified')
        site_content = body.find('div', class_='site-content')
        events_column = site_content.find(
            'div', class_='layout layout-one-column')
        events_index = events_column.find(
            'section', class_='calendar-events-index')
        calendar = events_index.find('div', {'data-react-class': 'Calendar'})

        # Create a json object for the calendar
        calendar_json = json.loads(calendar['data-react-props'])

        # Iterate through each event json
        for event_json in calendar_json['events']:
            # Extract important fields
            date = event_json['starts_at']
            currency_code = event_json['currency_code']
            impact = event_json['impact']
            actual = event_json['actual']
            forecast = event_json['forecast']
            previous = event_json['previous']
            all_day = event_json['all_day']

            # Construct a new "row" to add to the final dataframe
            new_row = [date, currency_code, impact,
                       actual, forecast, previous, all_day]

            # Add the row
            event_data.append(new_row)

    else:
        raise Exception(
            f'Request was denied -- error code = {resp.status_code}\n{resp.content}')


if __name__ == '__main__':
    # Parameters that affect which data is pulled from the economic calendar and how it is stored
    SAVE_EVENT_DF_AS_CSV = True  # True/False flag for saving the data to a csv file
    GET_CURRENT_WEEK = True  # True/False flag for just grabbing the most recent data from this week
    YEAR_RANGE = range(2018, 2023)  # Year range for downloading historical data (only used if the GET_CURRENT_WEEK flag is False)

    # Get most recent data
    if GET_CURRENT_WEEK:
        iso_calendar = datetime.utcnow().isocalendar()
        year, week_number, _ = iso_calendar

        response = requests.get(
            f'https://www.babypips.com/economic-calendar?week={year}-W{week_number}')

        parse_response(response)

    # Otherwise, get historical data
    else:
        curr_date = datetime.now()

        for year in YEAR_RANGE:
            date = datetime(year, 1, 1, hour=0,
                            minute=0, second=0, microsecond=0)

            while date.year == year and date <= curr_date:
                _, week_number, _ = date.isocalendar()

                # Make sure the week number contains 2 digits
                if week_number < 10:
                    week_number = f'0{week_number}'

                response = requests.get(
                    f'https://www.babypips.com/economic-calendar?week={year}-W{week_number}')

                parse_response(response)
                date += timedelta(weeks=1)

    # Convert event data to a dataframe
    event_data = np.array(event_data)
    event_df = pd.DataFrame(event_data, columns=[
                            'Date', 'Currency_Code', 'Impact', 'Actual', 'Forecast', 'Previous', 'All_Day'])
    event_df.reset_index(drop=True, inplace=True)

    # Save the dataframe as a csv file
    if SAVE_EVENT_DF_AS_CSV:
        event_df.to_csv('./events.csv', index=False)

    # Otherwise, print the first and last 5 rows of the dataframe
    else:
        print(event_df.head())
        print('-----------------------------------------------------------------')
        print(event_df.tail())
