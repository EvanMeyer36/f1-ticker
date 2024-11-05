import time
import requests
import feedparser
import schedule
from RPLCD.i2c import CharLCD
import RPi.GPIO as GPIO

lcd = CharLCD('PCF8574', 0x27)

# LCD constants
LCD_WIDTH = 16  # Width of the LCD display

# GPIO setup
BUTTON_REFRESH = 17
BUTTON_TOGGLE = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_REFRESH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_TOGGLE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# State variables
feeds = ["news", "race_results", "standings"]
current_feed_index = 0
toggle_feature_state = False

# Fetch race results from the Jolpica-F1 API
def fetch_race_data():
    url = "http://ergast.com/api/f1/current/last/results.json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print("Error fetching race data")
            return None
    except Exception as e:
        print("Error:", e)
        return None

def get_race_results(data):
    results = []
    if data:
        race_name = data['MRData']['RaceTable']['Races'][0]['raceName']
        race_results = data['MRData']['RaceTable']['Races'][0]['Results']
        results.append(f"Race: {race_name}")
        for result in race_results:
            position = result['position']
            driver = result['Driver']['familyName']
            results.append(f"{position}: {driver}")
    return results

# Fetch championship standings (drivers)
def fetch_standings_data():
    url = "http://ergast.com/api/f1/current/driverStandings.json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print("Error fetching standings data")
            return None
    except Exception as e:
        print("Error:", e)
        return None

def get_standings(data):
    standings = []
    if data:
        driver_standings = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
        standings.append("Driver Standings")
        for standing in driver_standings:
            position = standing['position']
            driver = standing['Driver']['familyName']
            points = standing['points']
            standings.append(f"{position}: {driver} {points}pts")
    return standings

# Fetch news from GPBlog
def fetch_news():
    feed_url = "https://www.gpblog.com/en/rss"
    feed = feedparser.parse(feed_url)
    headlines = [entry.title for entry in feed.entries]
    return headlines

# Display the selected feed
def display_feed():
    global current_feed_index
    lcd.clear()
    
    if feeds[current_feed_index] == "news":
        items = fetch_news()
    elif feeds[current_feed_index] == "race_results":
        race_data = fetch_race_data()
        items = get_race_results(race_data)
    elif feeds[current_feed_index] == "standings":
        standings_data = fetch_standings_data()
        items = get_standings(standings_data)
    else:
        items = ["No data"]

    # Display each item in the feed
    for item in items:
        lcd.clear()
        if len(item) > LCD_WIDTH:
            for i in range(len(item) - LCD_WIDTH + 1):
                lcd.write_string(item[i:i + LCD_WIDTH])
                time.sleep(0.3)
                lcd.clear()
        else:
            lcd.write_string(item)
            time.sleep(2)

# Button callbacks
def refresh_feed(channel):
    print("Refresh button pressed")
    lcd.clear()
    time.sleep(3)  # Pause to ensure the screen is cleanly wiped
    display_feed()

def toggle_feature(channel):
    global toggle_feature_state
    print("Toggle feature button pressed")
    lcd.clear()
    time.sleep(0.5)  # Pause to ensure the screen is cleanly wiped
    toggle_feature_state = not toggle_feature_state

# Setup event detection for buttons
GPIO.add_event_detect(BUTTON_REFRESH, GPIO.FALLING, callback=refresh_feed, bouncetime=300)
GPIO.add_event_detect(BUTTON_TOGGLE, GPIO.FALLING, callback=toggle_feature, bouncetime=300)

# Main loop to cycle through feeds
try:
    while True:
        display_feed()
        current_feed_index = (current_feed_index + 1) % len(feeds)  # Cycle to the next feed
        time.sleep(10)  # Delay between switching feeds
except KeyboardInterrupt:
    print("Cleaning up GPIO")
    GPIO.cleanup()
