import csv
import cv2
from collections import defaultdict

camera = "1"
date = "2015-11-12"
time = "0709"

img = cv2.imread(f'CNR-EXT_FULL_IMAGE_1000x750/FULL_IMAGE_1000x750/SUNNY/{date}/camera{camera}/{date}_{time}.jpg')
scale_percent = 259  # percent of original size
width = int(img.shape[1] * scale_percent / 100)
height = int(img.shape[0] * scale_percent / 100)
dim = (width, height)
img = cv2.resize(img, dim)
cameraSlots = defaultdict(list)
slotToLoc = {}

with open('CNR-EXT_FULL_IMAGE_1000x750/camera1.csv', newline='') as csvFile:
    cameraReader = csv.reader(csvFile)
    # SlotId,X,Y,W,H
    next(cameraReader)
    for row in cameraReader:
        # print(row)
        slotId, x, y, w, h = map(int, row)
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cameraSlots[camera].append(slotId)
        slotToLoc[slotId] = (x,y,w,h)

cv2.imwrite('dummy.jpg', img)

with open('CNRPark+EXT.csv', newline='') as csvFile:
    parkingReader = csv.reader(csvFile)
    # data is camera,datetime,day,hour,image_url,minute,month,occupancy,slot_id,weather,year,occupant_changed
    camera_ = "01"
    datetime_ = f'{date}_07.09'
    next(parkingReader)
    for row in parkingReader:

        camera, datetime, day, hour, image_url, minute, month, occupancy, slot_id, weather, year, occupant_changed = row
        
        if camera == camera_ and datetime == datetime_:
            print(slot_id, occupancy)
            x, y, w, h = slotToLoc[int(slot_id)]
            if occupancy == "0":
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            elif occupancy == "1":
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255), 2)
            else:
                raise Exception("wrong occupancy")

cv2.imwrite('dummy2.jpg', img)

