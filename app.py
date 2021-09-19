from flask import Flask, send_file
from flask_cors import CORS
import csv
from PIL import Image, ImageDraw
from collections import defaultdict
import base64
from io import BytesIO
from math import cos, asin, sqrt, pi
import json


def coord_distance(lat1, lon1, lat2, lon2):
    diameter_of_earth = 7917.5
    p = pi/180
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p) * \
        cos(lat2*p) * (1-cos((lon2-lon1)*p))/2
    return diameter_of_earth * asin(sqrt(a))

app = Flask(__name__)
CORS(app)

date_ = "2015-11-12"
year_ = "2015"
day_ = "12"
month_ = "11"

relevant_data_ = []
# cameras are all ints btw
# camera -> slot -> (x,y,w,h)
slot_to_loc = defaultdict(dict)
# camera -> date -> list of times
camera_date_to_times = defaultdict(lambda: defaultdict(list))

# initialization steps
for i in range(1, 10):
    with open(f'CNR-EXT_FULL_IMAGE_1000x750/camera{i}.csv', newline='') as csvFile:
        cameraReader = csv.reader(csvFile)
        # SlotId,X,Y,W,H
        next(cameraReader)
        for row in cameraReader:
            slotId, x, y, w, h = map(int, row)
            slot_to_loc[i][slotId] = (x, y, w, h)
with open('CNRPark+EXT.csv', newline='') as csvFile:
    parkingReader = csv.reader(csvFile)
    # data is camera,datetime,day,hour,image_url,minute,month,occupancy,slot_id,weather,year,occupant_changed
    next(parkingReader)
    for row in parkingReader:
        camera, datetime, day, hour, image_url, minute, month, occupancy, slot_id, weather, year, occupant_changed = row
        
        if year_ == year and month_ == month and day_ == day:
            camera = int(camera)
            # hour = int(hour)
            # minute = int(minute)
            assert(len(str(month)) == 2 and len(str(day)) == 2)
            hour = hour.zfill(2)
            minute = minute.zfill(2)
            assert(len(hour) == 2 and len(minute) == 2)
            date = f'{year}-{month}-{day}'
            camera_date_to_times[camera][date].append((hour, minute))
            relevant_data_.append(row)
for camera, date_to_times in camera_date_to_times.items():
    for date, times in date_to_times.items():
        times.sort()

print("Finished initialization")

# receive in the form "{hour}{minute}", 4 chars
# returns in the form "{hour}{minute}"
def get_nearest_time(camera, time):
    assert(len(time) == 4)
    hour = time[0:2]
    minute = time[2:4]
    pos_times = camera_date_to_times[int(camera)][date_]
    if len(times) == 0:
        raise Exception("No valid time!")
    best_time = (-1, -1)
    for i in range(len(pos_times)):
        pos_time = pos_times[i]
        if pos_time > (hour, minute):
            if i == 0:
                best_time = pos_times[-1]
                break
            else:
                best_time = pos_times[i-1]
                break
    if best_time == (-1, -1):
        best_time = pos_times[-1]
    (hour, minute) = best_time
    assert(len(hour) == 2 and len(minute) == 2)
    return f'{hour}{minute}'

def get_image(camera, time):
    img = Image.open(
        f'CNR-EXT_FULL_IMAGE_1000x750/FULL_IMAGE_1000x750/SUNNY/{date_}/camera{camera}/{date_}_{time}.jpg')
    scale_percent = 259  # percent of original size
    width = int(img.size[0] * scale_percent / 100)
    height = int(img.size[1] * scale_percent / 100)
    dim = (width, height)
    img = img.resize(dim)
    return img

def scale_down_image(img):
    scale_percent = 30  # percent of original size
    width = int(img.size[0] * scale_percent / 100)
    height = int(img.size[1] * scale_percent / 100)
    dim = (width, height)
    img = img.resize(dim)
    return img

def get_num_spaces(camera, time):
    camera_ = int(camera)
    hour = time[0:2]
    minute = time[2:4]
    datetime_ = f'{date_}_{hour}.{minute}'
    num_spaces = 0
    for row in relevant_data_:
        camera, datetime, day, hour, image_url, minute, month, occupancy, slot_id, weather, year, occupant_changed = row
        camera = int(camera)
        slot_id = int(slot_id)
        if camera == camera_ and datetime == datetime_:
            x, y, w, h = slot_to_loc[camera][slot_id]
            if occupancy == "0":
                num_spaces += 1
            elif occupancy == "1":
                pass
            else:
                raise Exception("wrong occupancy")
    return num_spaces

def draw_bounding_boxes(img, camera, time):
    camera_ = int(camera)
    hour = time[0:2]
    minute = time[2:4]
    datetime_ = f'{date_}_{hour}.{minute}'
    img_draw = ImageDraw.Draw(img)
    for row in relevant_data_:
        camera, datetime, day, hour, image_url, minute, month, occupancy, slot_id, weather, year, occupant_changed = row
        camera = int(camera)
        slot_id = int(slot_id)
        if camera == camera_ and datetime == datetime_:
            x, y, w, h = slot_to_loc[camera][slot_id]
            if occupancy == "0":
                img_draw.rectangle([(x, y), (x+w, y+h)], outline=(0,255,0), width=5)
            elif occupancy == "1":
                img_draw.rectangle([(x, y), (x+w, y+h)],
                                   outline=(255, 0, 0), width=5)
            else:
                raise Exception("wrong occupancy")
    return img

@app.route("/")
def hello_world():
    return "<p>Home page</p>"

@app.route("/num_spaces/<camera>/<time>")
def provide_num_spaces(camera, time):
    time = get_nearest_time(camera, time)
    num_spaces = get_num_spaces(camera, time)
    return str(num_spaces)

@app.route("/img/<camera>/<time>")
def provide_image(camera, time):
    time = get_nearest_time(camera, time)
    img = get_image(camera, time)
    img = draw_bounding_boxes(img, camera, time)
    buffered = BytesIO()
    img = scale_down_image(img)
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue())
    return img_str

@app.route("/get_best_parking/<lat>/<long>/<hours>/<minutes>")
def get_best_parking(lat, long, hours, minutes):
    print("Requested", lat, long)
    time = f'{hours.zfill(2)}{minutes.zfill(2)}'
    
    with open('cameras.json', 'r') as json_file:
        cameras = json.load(json_file)
    for camera in cameras:
        camera["distance"] = coord_distance(
            float(lat), float(long), float(camera["lat"]), float(camera["long"]))
        camera_id = int(camera["id"])
        camera_time = get_nearest_time(camera_id, time)
        camera["num_spots_available"] = get_num_spaces(camera_id, camera_time)
    cameras.sort(key= lambda camera: camera["distance"])
    return json.dumps(cameras)

    
    
