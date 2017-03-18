#!/usr/bin/env python
# -*- coding: utf8 -*-

"""

"""
import math
from PIL import Image
import os
import hashlib
import urllib2
import StringIO

class staticMapLite(object):
    def __init__(self):
        self.maxWidth = 1024
        self.maxHeight = 1024
        self.tileSize = 256
        self.tileSrcUrl = {
            'mapnik': 'http://tile.openstreetmap.org/{Z}/{X}/{Y}.png',
            'osmarenderer': 'http://otile1.mqcdn.com/tiles/1.0.0/osm/{Z}/{X}/{Y}.png',
            'cycle': 'http://a.tile.opencyclemap.org/cycle/{Z}/{X}/{Y}.png',
            'opentopomap':'http://a.tile.opentopomap.org/{Z}/{X}/{Y}.png',
        }
        self.tileDefaultSrc = 'mapnik'
        self.markerBaseDir = 'images/markers'
        self.errImg = 'images/err.png'
        self.osmLogo = 'images/osm_logo.png'
        self.markerPrototypes = {
            # found at http://www.mapito.net/map-marker-icons.html
            'lighblue': {'regex': '/^lightblue([0-9]+)$/',
                         'extension': '.png',
                         'shadow': False,
                         'offsetImage': '0,-19',
                         'offsetShadow': False
                         },
            # openlayers std markers
            'ol-marker': {'regex': '/^ol-marker(|-blue|-gold|-green)+$/',
                          'extension': '.png',
                          'shadow': '../marker_shadow.png',
                          'offsetImage': '-10,-25',
                          'offsetShadow': '-1,-13'
                          },
            # // taken from http://www.visual-case.it/cgi-bin/vc/GMapsIcons.pl
            'ylw': {'regex': '/^(pink|purple|red|ltblu|ylw)-pushpin$/',
                    'extension': '.png',
                    'shadow': '../marker_shadow.png',
                    'offsetImage': '-10,-32',
                    'offsetShadow': '-1,-13'
                    },
            # // http://svn.openstreetmap.org/sites/other/StaticMap/symbols/0.png
            'ojw': {'regex': '/^bullseye$/',
                    'extension': '.png',
                    'shadow': False,
                    'offsetImage': '-20,-20',
                    'offsetShadow': False
                    }
        }
        self.useTileCache = True
        self.tileCacheBaseDir = './cache/tiles'
        self.useMapCache = True
        self.mapCacheBaseDir = './cache/maps'
        self.mapCacheID = ''
        self.mapCacheFile = ''
        self.mapCacheExtension = 'png'
        # protected $zoom, $lat, $lon, $width, $height, $markers, $image, $maptype;
        # protected $centerX, $centerY, $offsetX, $offsetY;
        self.zoom = 0
        self.lat = 0
        self.lon = 0
        self.width = 500
        self.height = 350
        self.markers = []
        self.maptype = self.tileDefaultSrc
        self.needDebug=True

    def debug(self,s):
        if self.needDebug:
            print s
    def parseParams(self,params):
        if params.get('show',"") != "":
            self.parseOjwParams(params)
        else:
            self.parseLiteParams(params)

    def parseLiteParams(self,params):
        # get zoom from GET paramter
        try:
            self.zoom = int(params['zoom'])
        except:
            self.zoom = 0
        if self.zoom > 18:
            self.zoom = 18
        #// get lat and lon from GET paramter
        (self.lat,self.lon) = params['center'].split(',',2)
        self.lat = float(self.lat)
        self.lon = float(self.lon)
        #// get size from GET paramter
        if params.get('size',False):
            (self.width, self.height) = params['size'].split('x',2)
            self.width = int(self.width)
            if self.width > self.maxWidth:
                self.width = self.maxWidth
            self.height = int(self.height)
            if self.height > self.maxHeight:
                self.height = self.maxHeight
        if params.get('markers',"") != '':
            markers = params['markers'].split('|')
            for marker in markers:
                markerLat, markerLon, markerType = marker.split(',',3)
                markerLat = float(markerLat)
                markerLon = float(markerLon)
                #markerType = basename($markerType); ???
                self.markers.append({'lat' : markerLat, 'lon':  markerLon, 'type': markerType})
        if params.get('maptype',False):
            if params['maptype'] in self.tileSrcUrl.keys():
                self.maptype = params['maptype']

    def parseOjwParams(self,params):
         self.lat = float(params['lat'])
         self.lon = float(params['lon'])
         self.zoom = int(params['z'])
         self.width = int(params['w'])
         if self.width > self.maxWidth:
             self.width = self.maxWidth
         self.height = int(params['h'])
         if self.height > self.maxHeight:
             self.height = self.maxHeight
         if params.get('mlat0','') != '':
             markerLat = float(params['mlat0'])
             if params.get('mlon0','') != "":
                 markerLon = float(params['mlon0']);
                 self.markers.append({'lat':markerLat, 'lon': markerLon, 'type' : "bullseye"})

    def lonToTile(self,long, zoom):
        return ((long + 180) / 360) * pow(2, zoom)

    def latToTile(self,lat,zoom):
        return (1 - math.log(math.tan(lat * math.pi / 180) + 1 / math.cos(lat * math.pi / 180)) / math.pi) / 2 * pow(2, zoom)

    def initCoords(self):
        self.centerX = self.lonToTile(self.lon, self.zoom)
        self.centerY = self.latToTile(self.lat, self.zoom)
        self.offsetX = math.floor((math.floor(self.centerX) - self.centerX) * self.tileSize)
        self.offsetY = math.floor((math.floor(self.centerY) - self.centerY) * self.tileSize)

    def createBaseMap(self):
        self.image = Image.new('RGB', (self.width, self.height))
        startX = int(math.floor(self.centerX - (self.width / self.tileSize) / 2))
        startY = int(math.floor(self.centerY - (self.height / self.tileSize) / 2))
        endX = int(math.ceil(self.centerX + (self.width / self.tileSize) / 2))
        endY = int(math.ceil(self.centerY + (self.height / self.tileSize) / 2))
        self.offsetX = self.offsetX-math.floor((self.centerX - math.floor(self.centerX)) * self.tileSize)
        self.offsetY = -math.floor((self.centerY - math.floor(self.centerY)) * self.tileSize)
        self.offsetX += math.floor(self.width / 2);
        self.offsetY += math.floor(self.height / 2);
        self.offsetX += math.floor(startX - math.floor(self.centerX)) * self.tileSize
        self.offsetY += math.floor(startY - math.floor(self.centerY)) * self.tileSize
        for x in range(startX,endX,1):
            for y in  range(startY,endY,1):
                url = self.tileSrcUrl[self.maptype]
                url = url.replace('{Z}',str(self.zoom))
                url = url.replace('{X}',str(x))
                url = url.replace('{Y}',str(y))
                self.debug(url)
                tileData = self.fetchTile(url)
                if (tileData):
                    tempBuff = StringIO.StringIO()
                    tempBuff.write(tileData)
                    tempBuff.seek(0)
                    im=Image.open(tempBuff)
                else:
                     im=Image.open(self.errImg)
                destX = int((x - startX) * self.tileSize + self.offsetX)
                destY = int((y - startY) * self.tileSize + self.offsetY)
                #imagecopy(self.image, $tileImage, $destX, $destY, 0, 0, self.tileSize, self.tileSize);
                self.image.paste(im, (destX,destY))

    def placeMarkers(self):
        pass

    def tileUrlToFilename(self,url):
        url = url.replace('http://','')
        return self.tileCacheBaseDir + "/" +url

    def checkTileCache(self,url):
        filename = self.tileUrlToFilename(url)
        if os.path.exists(filename):
            return open(filename).read()

    def checkMapCache(self):
        self.mapCacheID = hashlib.md5(self.serializeParams()).hexdigest()
        filename = self.mapCacheIDToFilename()
        if (os.path.exists(filename)):
            return True

    def serializeParams(self):
        return "&".join([str(self.zoom), str(self.lat), str(self.lon), str(self.width), str(self.height), str(self.markers), self.maptype])

    def mapCacheIDToFilename(self):
        if not self.mapCacheFile:
            self.mapCacheFile = self.mapCacheBaseDir +"/" + self.maptype + "/" + str(self.zoom) + \
                                "/cache_" + self.mapCacheID[0: 2] + "/" + self.mapCacheID[2:2] + "/" + self.mapCacheID[4:]
        return self.mapCacheFile + "." +self.mapCacheExtension

    def mkdir_recursive(self,pathname, mode=0o777):
        try:
            os.makedirs(pathname,mode)
        except:
            pass

    def writeTileToCache(self,url, data):
        filename = self.tileUrlToFilename(url)
        path = os.path.dirname(filename.rstrip(os.pathsep)) or '.'
        self.mkdir_recursive(path)
        f = open(filename, 'w')
        f.write(data)
        f.close()

    def fetchTile(self,url):
        cached = self.checkTileCache(url)
        if (self.useTileCache and cached):
            return cached
        tile =urllib2.urlopen(url).read()
        if (tile and self.useTileCache):
            self.writeTileToCache(url, tile)
        return tile

    def copyrightNotice(self):
        #logoImg = imagecreatefrompng(self.osmLogo);
        #imagecopy($this->image, $logoImg, imagesx($this->image) - imagesx($logoImg), imagesy($this->image) - imagesy($logoImg), 0, 0, imagesx($logoImg), imagesy($logoImg));
        pass

    def sendHeader(self):
        """
        header('Content-Type: image/png');
        $expires = 60 * 60 * 24 * 14;
        header("Pragma: public");
        header("Cache-Control: maxage=" . $expires);
        header('Expires: ' . gmdate('D, d M Y H:i:s', time() + $expires) . ' GMT');
        """
        pass
    def makeMap(self):
        self.initCoords()
        self.createBaseMap()
        if len(self.markers) > 0:
            self.placeMarkers()
        if self.osmLogo:
            self.copyrightNotice()

    def showMap(self,params):
        self.parseParams(params)
        if self.useMapCache:
            # use map cache, so check cache for map
            if not self.checkMapCache():
                #// map is not in cache, needs to be build
                self.makeMap()
                path = os.path.dirname(self.mapCacheIDToFilename().rstrip(os.pathsep)) or '.'
                self.mkdir_recursive(path)
                #imagepng($this->image, $this->mapCacheIDToFilename(), 9);
                self.sendHeader()
                if os.path.exists(self.mapCacheIDToFilename()):
                    return open(self.mapCacheIDToFilename(),'r').read()
                else:
                    return self.image.save(self.mapCacheIDToFilename())
            else:
                #// map is in cache
                self.sendHeader()
                data = open(self.mapCacheIDToFilename(),'r').read()
                return data
        else:
            #// no cache, make map, send headers and deliver png
            self.makeMap()
            self.sendHeader()
            #return imagepng($this->image);
            return ""

if __name__ == "__main__":
    params = {
        'center': '56.905628,60.387039',
        'zoom': '15',
        'size': '1024x1024',
        'maptype': 'opentopomap',
        'markers': '40.702147,-74.015794,blues|40.711614,-74.012318,greeng|40.718217,-73.998284,redc'
    }
    map = staticMapLite()
    map.showMap(params)
