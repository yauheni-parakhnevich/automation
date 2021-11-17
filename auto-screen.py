#!/usr/bin/env python
# coding: utf-8

import sys
import os
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'images')
fontdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fonts')
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from influxdb import InfluxDBClient
import logging
from waveshare_epd import epd7in5b_HD
import time

class Measure:
    temperature = 0
    humidity = 0

def get_moisture(alias):
    results = client.query('select last("Moisture") from "Flowers" where alias = \'' + alias + '\'')
    return results.raw['series'][0]['values'][0][1]

def get_measure(alias):
    results = client.query('select last("Temperature") as temperature,last( "Humidity") as humidity from Telemetry where alias = \'' + alias + '\'')
    measure = Measure()
    measure.temperature = results.raw['series'][0]['values'][0][1]
    measure.humidity = results.raw['series'][0]['values'][0][2]
    
    return measure

def getLevelIcon(level):
    if level < 10:
        return levelIcons[0]
    elif level < 13:
        return levelIcons[1]
    elif level < 16:
        return levelIcons[2]    
    elif level < 19:
        return levelIcons[3]
    else:
        return levelIcons[4]

def humidity_color(humidity):
    if humidity < 40 or humidity > 60:
        return 'red'
    else:
        return 'black'

logging.basicConfig(level=logging.DEBUG)

logging.info("Reading fonts and images")

fnt = ImageFont.truetype(os.path.join(fontdir, "HelveticaNeueCyr-Medium.ttf"), 80)
fntHeader = ImageFont.truetype(os.path.join(fontdir, "HelveticaNeueCyr-Medium.ttf"), 20)

humidityIcon = Image.open('images/humidity.png', 'r')
temperatureIcon = Image.open('images/temperature.png', 'r')
oliveIcon = Image.open('images/olive.png', 'r')
oleandrIcon = Image.open('images/oleandr.png', 'r')

levelIcons = [Image.open('images/level1.png', 'r'), Image.open('images/level2.png', 'r'), Image.open('images/level3.png', 'r'), Image.open('images/level4.png', 'r'), Image.open('images/level5.png', 'r')]

size = (880, 528)
cornersLeft = [(18, 20), (305, 20), (592, 20), (18, 274), (305, 274), (592, 274)]
cardSize = (270, 234)
headerSize = (190, 30)

logging.info("Init screen")
epd = epd7in5b_HD.EPD()

logging.info("Screen size: ")
logging.info((epd.width, epd.height))

logging.info("Prepare the screen")
epd.init()

try:
    while True:
        try:
            logging.info("Connecting to the database")
            client = InfluxDBClient(host='192.168.13.30', port=8086)
            client.switch_database('garden')

            logging.info("Reading measures")
            workRoom = get_measure('workRoomTempSensor')
            livRoom = get_measure('livRoomTempSensor')
            SashaRoom = get_measure('SashaRoomTempSensor')
            bedRoom = get_measure('bedRoomTempSensor')

            oleandrMoisture = get_moisture('flowerOleandrSensor')
            olivaMoisture = get_moisture('flowerOlivaSensor')

            temperature = [workRoom.temperature, bedRoom.temperature, livRoom.temperature, SashaRoom.temperature]
            humidity = [workRoom.humidity, bedRoom.humidity, livRoom.humidity, SashaRoom.humidity]
            flowers = [oleandrMoisture, olivaMoisture]

            logging.info("Temperature")
            logging.info(temperature)

            logging.info("Humidity")
            logging.info(humidity)

            logging.info("Flowers")
            logging.info(flowers)

            logging.info("Preparing image")
            img = Image.new('RGB', size, color = 'white')
            img_red = Image.new('1', size, 255)
            draw = ImageDraw.Draw(img)
            draw_red = ImageDraw.Draw(img_red)

            for i in range(6):
                draw.rectangle([cornersLeft[i], tuple(np.add(cornersLeft[i], cardSize))], fill = 'white', outline = 'black')
                draw.rectangle([tuple(np.add(cornersLeft[i], (70, 0))), tuple(np.add(cornersLeft[i], headerSize))], fill = 'white', outline = 'black')

            for i in range(4):
                img.paste(temperatureIcon, tuple(np.add(cornersLeft[i], (41, 59))))
                img.paste(humidityIcon, tuple(np.add(cornersLeft[i], (38, 144))))

            img.paste(oliveIcon, (595, 336))
            img.paste(oleandrIcon, (308, 336))

            draw.text((103, 27), 'КАБИНЕТ', font = fntHeader, fill = 'black')
            draw.text((387, 27), 'СПАЛЬНЯ', font = fntHeader, fill = 'black')
            draw.text((700, 27), 'ЗАЛ', font = fntHeader, fill = 'black')
            draw.text((105, 281), 'ПЕЩЕРА', font = fntHeader, fill = 'black')
            draw.text((387, 281), 'ОЛЕАНДР', font = fntHeader, fill = 'black')
            draw.text((685, 281), 'ОЛИВА', font = fntHeader, fill = 'black')

            img.paste(getLevelIcon(flowers[0]), (450, 361))
            img.paste(getLevelIcon(flowers[1]), (735, 361))

            for i in range(4):
                draw.text(tuple(np.add(cornersLeft[i], (140, 62))), '{:2.0f}'.format(temperature[i]), font = fnt, fill = 'black')
                hum_color = humidity_color(humidity[i])
                if hum_color == 'red':
                    draw_red.text(tuple(np.add(cornersLeft[i], (140, 147))), '{:2.0f}'.format(humidity[i]), font = fnt, fill = 'black')
                else:
                    draw.text(tuple(np.add(cornersLeft[i], (140, 147))), '{:2.0f}'.format(humidity[i]), font = fnt, fill = humidity_color(humidity[i]))

            logging.info("Clearing the screen")
            epd.Clear()

            logging.info("Drawing the image")
            epd.display(epd.getbuffer(img), epd.getbuffer(img_red))
        except Exception:
            logging.info("Got exception during data loading, skipping refresh...")

        time.sleep(600)

except KeyboardInterrupt:
    logging.info("Stopping...")
