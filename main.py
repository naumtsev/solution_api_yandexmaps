import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow,QTableWidgetItem, QPushButton, QLabel, QDateEdit, QHBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
from PyQt5 import QtWidgets, Qt, QtCore
from requests import get, post, put
import requests
import argparse
import os
FILE_NAME = 'map.jpg'
TYPEOFMAP = 'sat'
PARAMS = ''
SIZE_STRING = '&size=500,350'
GLOBAL_FLAG = False
PG = ''
PG_ARRAY = []

def size_to_need(sz):
    w, h = map(float, sz.split(','))
    near = ''
    delta = 1e6
    for w2, h2 in PG_ARRAY:
        if abs(w2 - w) <= delta:
            delta = abs(w2 - w)
            near = str(w2) + ',' + str(h2)
    return near

def update_PG():
    #2, 0.5
    w, h = map(float, PG.split(','))
    while(not (w * 0.5 < 0.0003 or h * 0.5 < 0.0003)):
        w,h = w * 0.5, h * 0.5

    while(not (h * 2 > 150 or w * 2 > 150)):
        PG_ARRAY.append((w, h))
        w *= 2
        h *= 2

def search_organization(cord):
    search_api_server = "https://search-maps.yandex.ru/v1/"
    api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
    address_ll = cord
    delt = 50 / (111000)
    spn = str(delt) + ',' + str(delt)
    search_params = {
            "apikey": api_key,
            "lang": "ru_RU",
            "ll": address_ll,
            "spn": spn,
            "type": "biz"}

    response = requests.get(search_api_server, params=search_params).json()
    if(len(response['features'])):
        return response['features'][0]['properties']['CompanyMetaData']['name']
    return ''


def size(response_my):
    resp = response_my['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['boundedBy']['Envelope']
    lx, ly = map(float, resp['lowerCorner'].split())
    rx, ry = map(float, resp['upperCorner'].split())
    w = abs(rx - lx)
    h = abs(ry - ly)
    return (w, h)

def search(place):
    geocoder_request = "http://geocode-maps.yandex.ru/1.x/?geocode={}&format=json".format(place)
    response = get(geocoder_request)
    js = response.json()
    w, h = size(js)
    json_response = js['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
    x, y = json_response.split()
    gg = max(w, h)

    w = gg
    h = w * 350 / 500
    if GLOBAL_FLAG:
        global PG
        PG = size_to_need( str(w) + ',' + str(h))
        return str(x) + ',' + str(y), PG

    return str(x) + ',' + str(y), str(w) + ',' + str(h)



def get_image_by_adress(name):
    cord, size  = search(name)
    map_request = "http://static-maps.yandex.ru/1.x/?l={}&ll={}&spn={}".format(TYPEOFMAP, cord, size) + PARAMS + SIZE_STRING
    pg = size
    response = requests.get(map_request)
    map_file = FILE_NAME
    with open(map_file, "wb") as file:
        file.write(response.content)
    return (map_file, cord, pg)

def get_image_by_cord(cord, size):
    map_request = "http://static-maps.yandex.ru/1.x/?l={}&ll={}&spn={}".format(TYPEOFMAP, cord, size)  + PARAMS + SIZE_STRING
    response = requests.get(map_request)
    map_file = FILE_NAME
    with open(map_file, "wb") as file:
        file.write(response.content)
    return (map_file, cord, size)






class Example(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('uifile.ui', self)
        self.cord = None
        self.pg = None
        self.my_init()
        self.postcode = ''
        self.flag_postcode = False

        for i in self.pgbuttons.buttons():
            i.clicked.connect(self.changepg)

        for i in self.leftrightbuttons.buttons():
                i.clicked.connect(self.pushleftandright)

        for i in self.updownbuttons.buttons():
            i.clicked.connect(self.pushupdown)

        for i in self.switchertypemap.buttons():
            i.clicked.connect(self.change_type_of_map)

        for i in self.switcherpostcode.buttons():
           i.clicked.connect(self.change_post_code)

        self.radioButton_5.setChecked(True)
        self.radioButton_2.setChecked(True)

        self.searchbutton.clicked.connect(self.search_object)
        self.pushButton_8.clicked.connect(self.reset_objects)


    def my_init(self):
        hbox = QHBoxLayout(self)
        place = 'Ульяновск'
        file_name, cord, pg = get_image_by_adress(place)
        global GLOBAL_FLAG, PG
        GLOBAL_FLAG = True
        PG = pg
        update_PG()

        self.cord = cord
        self.pg = pg
        pixmap = QPixmap(file_name).scaled(500,350)

        self.lbl = QLabel(self)
        self.lbl.setPixmap(pixmap)
        self.lbl.resize(500, 350)
        hbox.addWidget(self.lbl)
        self.lbl.move(20, 20)
        self.setLayout(hbox)
        self.move(0, 0)
        self.show()

    def changepg(self):
        pg = float(self.sender().whatsThis())
        w, h = map(float, self.pg.split(','))
        if(w * pg < 0.0003 or h * pg < 0.0003  or h * pg > 150 or w * pg > 150 ):
            return

        w *= pg
        h *= pg
        self.pg = str(w) + ',' + str(h)
        get_image_by_cord(self.cord, self.pg)
        self.update_image()


    def pushleftandright(self):
        c = float(self.sender().whatsThis())
        w, h = map(float, self.pg.split(','))
        dw, dh = w / 4, h / 4
        x, y = map(float, self.cord.split(','))
        if (x + dw * c > 180 or x + dw * c < -180):
            return
        x = x + dw * c
        self.cord = str(x) + ',' + str(y)
        get_image_by_cord(self.cord, self.pg)
        self.update_image()

    def pushupdown(self):
        c = float(self.sender().whatsThis())
        w, h = map(float, self.pg.split(','))
        dw, dh = w / 4, h / 4
        x, y = map(float, self.cord.split(','))
        if (y + dh * c > 80 or y + dh * c < -80):
            return
        y = y + dh * c
        self.cord = str(x) + ',' + str(y)


        get_image_by_cord(self.cord, self.pg)
        self.update_image()


    def update_image(self):
        pixmap = QPixmap(FILE_NAME)
        self.lbl.setPixmap(pixmap)

    def change_type_of_map(self):
        new_type = self.sender().whatsThis()
        global FILE_NAME
        os.remove(FILE_NAME)
        if new_type == 'sat':
            FILE_NAME = 'sat.jpg'
        elif new_type =='map':
            FILE_NAME = 'map.png'
        elif new_type == 'sat,skl':
            FILE_NAME = 'sat_skl.jpg'

        global TYPEOFMAP
        TYPEOFMAP = new_type
        get_image_by_cord(self.cord, self.pg)
        self.update_image()


    def search_object(self):
        text = self.gps_lbl.text()
        try:
            file_name, cord, pg = get_image_by_adress(text)
            global PARAMS
            PARAMS='&pt={},pm2rdm'.format(cord)
            self.pg = pg
            get_image_by_cord(cord, pg)
            self.cord = cord
            self.update_image()

            test = 'https://geocode-maps.yandex.ru/1.x/?geocode={}&format=json'.format(self.cord)
            tt = get(test).json()

            req = tt['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
                'GeocoderMetaData']['text']
            self.adress_lbl.setText(req)
            self.postcode = tt['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['Address']['postal_code']
            self.update_postcode()
        except:
            return

    def reset_objects(self):
        global PARAMS
        PARAMS = ''
        self.gps_lbl.setText('')
        get_image_by_cord(self.cord, self.pg)
        self.update_image()
        self.adress_lbl.setText('')
        self.flag_postcode = False
        self.radioButton_5.setChecked(True)
        self.postcode = ''
        self.update_postcode()

    def change_post_code(self):
        flag = int(self.sender().whatsThis())
        self.flag_postcode = flag
        self.update_postcode()

    def update_postcode(self):
        if self.flag_postcode:
            self.postcodelbl.setText(self.postcode)
        else:
            self.postcodelbl.setText('')

    def mouseReleaseEvent(self, e):
        global PARAMS
        x, y = e.pos().x(), e.pos().y()
        if e.button() == Qt.Qt.LeftButton:
            if (x >= 20 and x <= 500 + 20 and  y >= 20 and y <= 350 + 20):
                x -= 20
                y -= 20

                w, h = map(float, self.pg.split(','))
                deltaw = (w * x / 500 - w  / 2) * 2.86
                deltah = (h / 2 -  h * y / 350) * 1.78
                nowx, nowy = map(float, self.cord.split(','))
                newx = nowx + deltaw
                newy = nowy + deltah
                new_cord = str(newx) + ',' + str(newy)

                PARAMS = '&pt={},pm2am'.format(new_cord)

                try:
                        print(new_cord)
                        test = 'https://geocode-maps.yandex.ru/1.x/?geocode={}&format=json'.format(new_cord)
                        tt = get(test).json()
                        get_image_by_cord(self.cord, self.pg)
                        self.update_image()
                        req = tt['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
                               'GeocoderMetaData']['text']


                        self.adress_lbl.setText(req)

                        self.postcode = \
                        tt['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
                           'GeocoderMetaData']['Address']['postal_code']
                        self.update_postcode()
                except:
                    return
            else:
                return

        elif e.button() == Qt.Qt.RightButton:
            if (x >= 20 and x <= 500 + 20 and  y >= 20 and y <= 350 + 20):
                x -= 20
                y -= 20
                w, h = map(float, self.pg.split(','))
                deltaw = (w * x / 500 - w  / 2) * 2.86
                deltah = (h / 2 -  h * y / 350) * 1.78
                nowx, nowy = map(float, self.cord.split(','))
                newx = nowx + deltaw
                newy = nowy + deltah
                new_cord = str(newx) + ',' + str(newy)
                PARAMS = '&pt={},pm2am'.format(new_cord)

                try:

                        test = 'https://geocode-maps.yandex.ru/1.x/?geocode={}&format=json'.format(new_cord)
                        tt = get(test).json()
                        get_image_by_cord(self.cord, self.pg)
                        self.update_image()
                        req = tt['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
                               'GeocoderMetaData']['text']
                        org = search_organization(new_cord)
                        if org:
                            self.adress_lbl.setText(req + '\n' + 'Организация: ' + org)
                        else:
                            self.adress_lbl.setText(req)
                        self.postcode = \
                        tt['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
                           'GeocoderMetaData']['Address']['postal_code']
                        self.update_postcode()
                except:
                    return
        return

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())



