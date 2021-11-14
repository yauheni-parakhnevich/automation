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

client = InfluxDBClient(host='192.168.13.30', port=8086)

client.switch_database('garden')

workRoom = get_measure('workRoomTempSensor')
livRoom = get_measure('livRoomTempSensor')
SashaRoom = get_measure('SashaRoomTempSensor')
bedRoom = get_measure('bedRoomTempSensor')

oleandrMoisture = get_moisture('flowerOleandrSensor')
olivaMoisture = get_moisture('flowerOlivaSensor')

temperature = [workRoom.temperature, bedRoom.temperature, livRoom.temperature, SashaRoom.temperature]
humidity = [workRoom.humidity, bedRoom.humidity, livRoom.humidity, SashaRoom.humidity]
flowers = [oleandrMoisture, olivaMoisture]

fnt = ImageFont.truetype(os.path.join(fontdir, "HelveticaNeueCyr-Medium.ttf"), 80)
fntHeader = ImageFont.truetype(os.path.join(fontdir, "HelveticaNeueCyr-Medium.ttf"), 20)

humidityIcon = Image.open('images/humidity.png', 'r')
temperatureIcon = Image.open('images/temperature.png', 'r')
oliveIcon = Image.open('images/olive.png', 'r')
oleandrIcon = Image.open('images/oleandr.png', 'r')

levelIcons = [Image.open('images/level1.png', 'r'), Image.open('images/level2.png', 'r'), Image.open('images/level3.png', 'r'), Image.open('images/level4.png', 'r'), Image.open('images/level5.png', 'r')]

size = (800, 480)
cornersLeft = [(12, 20), (275, 20), (538, 20), (12, 250), (275, 250), (538, 250)]
cardSize = (250, 210)
headerSize = (180, 30)

img = Image.new('RGB', size, color = 'white')
draw = ImageDraw.Draw(img)

for i in range(6):
    draw.rectangle([cornersLeft[i], tuple(np.add(cornersLeft[i], cardSize))], fill = 'white', outline = 'black')
    draw.rectangle([tuple(np.add(cornersLeft[i], (70, 0))), tuple(np.add(cornersLeft[i], headerSize))], fill = 'white', outline = 'black')
    
for i in range(4):
    img.paste(temperatureIcon, tuple(np.add(cornersLeft[i], (41, 47))))
    img.paste(humidityIcon, tuple(np.add(cornersLeft[i], (38, 132))))

img.paste(oliveIcon, (543, 300))
img.paste(oleandrIcon, (278, 300))

draw.text((92, 27), 'КАБИНЕТ', font = fntHeader, fill = 'black')
draw.text((352, 27), 'СПАЛЬНЯ', font = fntHeader, fill = 'black')
draw.text((643, 27), 'ЗАЛ', font = fntHeader, fill = 'black')
draw.text((92, 257), 'ПЕЩЕРА', font = fntHeader, fill = 'black')
draw.text((352, 257), 'ОЛЕАНДР', font = fntHeader, fill = 'black')
draw.text((628, 257), 'ОЛИВА', font = fntHeader, fill = 'black')

for i in range(4):
    draw.text(tuple(np.add(cornersLeft[i], (140, 50))), '{:2.0f}'.format(temperature[i]), font = fnt, fill = 'black')
    draw.text(tuple(np.add(cornersLeft[i], (140, 132))), '{:2.0f}'.format(humidity[i]), font = fnt, fill = humidity_color(humidity[i]))

img.paste(getLevelIcon(flowers[0]), (417, 325))
img.paste(getLevelIcon(flowers[1]), (680, 325))

epd = epd7in5b_HD.EPD()

logging.info("init and Clear")
epd.init()
epd.Clear()

epd.display(epd.getbuffer(img))