#!/usr/bin/env python
# -*- coding: utf8 -*-

"""

"""
import math
import ssl
from PIL import Image, ImageFont, ImageDraw
import os
import hashlib
import urllib2
import StringIO
import random
import re


class staticMapLite(object):
    def __init__(self):
        self.maxWidth = 10240
        self.maxHeight = 10240
        self.tileSize = 256
        self.tileSrcUrl = {
            'mapnik': {
                'url': 'http://tile.openstreetmap.org/{Z}/{X}/{Y}.png',
                'copyright': "(c) Data OpenStreetMap ",
            },
            'osmarenderer': {
                'url': 'http://otile1.mqcdn.com/tiles/1.0.0/osm/{Z}/{X}/{Y}.png',
                'copyright': "(c) Data OpenStreetMap",
            },
            'cycle': {
                'url': 'http://{ABC}.tile.opencyclemap.org/cycle/{Z}/{X}/{Y}.png',
                'copyright': "(c) Data OpenStreetMap", },
            'opentopomap': {
                'url': 'https://{ABC}.tile.opentopomap.org/{Z}/{X}/{Y}.png',
                'copyright': "(c) Data OpenStreetMap, NASA SRTM", }
        }
        self.tileDefaultSrc = 'mapnik'
        self.markerBaseDir = 'images/markers'
        self.errImg = 'images/err.png'
        self.osmLogo = 'images/osm_logo.png'
        self.markerPrototypes = {
            # found at http://www.mapito.net/map-marker-icons.html
            'lighblue': {'regex': "^lightblue([0-9]+)$",
                         'extension': '.png',
                         'shadow': False,
                         'offsetImage': '0,-19',
                         'offsetShadow': False
                         },
            # openlayers std markers
            'ol-marker': {'regex': "^ol-marker(|-blue|-gold|-green)+$",
                          'extension': '.png',
                          'shadow': '../marker_shadow.png',
                          'offsetImage': '-10,-25',
                          'offsetShadow': '-1,-13'
                          },
            # // taken from http://www.visual-case.it/cgi-bin/vc/GMapsIcons.pl
            'ylw': {'regex': "^(pink|purple|red|ltblu|ylw)-pushpin$",
                    'extension': '.png',
                    'shadow': '../marker_shadow.png',
                    'offsetImage': '-10,-32',
                    'offsetShadow': '-1,-13'
                    },
            # // http://svn.openstreetmap.org/sites/other/StaticMap/symbols/0.png
            'ojw': {'regex': "^bullseye$",
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
        self.zoom = 0
        self.lat = 0
        self.lon = 0
        self.width = 500
        self.height = 350
        self.markers = []
        self.image = None
        self.centerX = 0
        self.centerY = 0
        self.offsetX = 0
        self.offsetY = 0
        self.maptype = self.tileDefaultSrc
        self.needDebug = True
        self.font = "fonts/Roboto-Black.ttf"
        self.fontColor = (0, 0, 0)
        self.fontSize = 10

    def debug(self, s):
        if self.needDebug:
            print s

    def parseParams(self, params):
        if params.get('show', "") != "":
            self.parseOjwParams(params)
        else:
            self.parseLiteParams(params)

    def parseLiteParams(self, params):
        # get zoom from GET paramter
        self.zoom = int(params.get('zoom', '0'))
        if self.zoom > 18:
            self.zoom = 18
        # // get lat and lon from GET paramter
        (self.lat, self.lon) = params['center'].split(',', 2)
        self.lat = float(self.lat)
        self.lon = float(self.lon)
        # // get size from GET paramter
        if params.get('size', False):
            (self.width, self.height) = params['size'].split('x', 2)
            self.width = int(self.width)
            if self.width > self.maxWidth:
                self.width = self.maxWidth
            self.height = int(self.height)
            if self.height > self.maxHeight:
                self.height = self.maxHeight
        if params.get('markers', "") != '':
            markers = params['markers'].split('|')
            for marker in markers:
                markerLat, markerLon, markerType = marker.split(',', 3)
                markerLat = float(markerLat)
                markerLon = float(markerLon)
                # markerType = basename($markerType); ???
                self.markers.append({'lat': markerLat, 'lon': markerLon, 'type': markerType})
        if params.get('maptype', False):
            if params['maptype'] in self.tileSrcUrl.keys():
                self.maptype = params['maptype']

    def parseOjwParams(self, params):
        self.lat = float(params['lat'])
        self.lon = float(params['lon'])
        self.zoom = int(params['z'])
        self.width = int(params['w'])
        if self.width > self.maxWidth:
            self.width = self.maxWidth
        self.height = int(params['h'])
        if self.height > self.maxHeight:
            self.height = self.maxHeight
        if params.get('mlat0', '') != '':
            markerLat = float(params['mlat0'])
            if params.get('mlon0', '') != "":
                markerLon = float(params['mlon0']);
                self.markers.append({'lat': markerLat, 'lon': markerLon, 'type': "bullseye"})

    def lonToTile(self, long, zoom):
        return ((long + 180) / 360) * pow(2, zoom)

    def latToTile(self, lat, zoom):
        return (1 - math.log(math.tan(lat * math.pi / 180) + 1 / math.cos(lat * math.pi / 180)) / math.pi) / 2 * pow(2,
                                                                                                                     zoom)
    def lonToPix(self,lon):
        """
        Dest X
        :param lon:
        :return:
        """
        self.debug('lonToPix:')
        self.debug('in lon:'+str(lon))
        self.debug('int(math.floor((self.width / 2) - self.tileSize * (self.centerX - self.lonToTile(lon, self.zoom))))')
        self.debug('int(math.floor(('+str(self.width)+' / 2) - '+str(self.tileSize)+' * ('+str(self.centerX)+' - '+str(self.lonToTile(lon, self.zoom))+'))')
        self.debug(self.lonToTile(lon, self.zoom))
        return int(math.floor((self.width / 2) - self.tileSize * (self.centerX - self.lonToTile(lon, self.zoom))))

    def latToPix(self,lat):
        """
        Dest Y
        :param lat:
        :return:
        """
        self.debug('latToPix:')
        self.debug('in lat:'+str(lat))
        self.debug('int(math.floor((self.height / 2) - self.tileSize * (self.centerY - self.latToTile(lat, self.zoom))))')
        self.debug('int(math.floor(('+str(self.height) +' / 2) - '+str(self.tileSize)+' * ('+str(self.centerY)+' - '+str(self.latToTile(lat, self.zoom))+')))')
        return int(math.floor((self.height / 2) - self.tileSize * (self.centerY - self.latToTile(lat, self.zoom))))

    def coordsToPix(self,lat,lon):
        """

        :param lat:
        :param lon:
        :return: ( lat, lon )
        """
        return (self.latToPix(lat),self.lonToPix(lon))

    def initCoords(self):
        self.centerX = self.lonToTile(self.lon, self.zoom)
        self.centerY = self.latToTile(self.lat, self.zoom)
        self.offsetX = math.floor((math.floor(self.centerX) - self.centerX) * self.tileSize)
        self.offsetY = math.floor((math.floor(self.centerY) - self.centerY) * self.tileSize)

    def createBaseMap(self):
        self.image = Image.new('RGBA', (self.width, self.height))
        startX = int(math.floor(self.centerX - (self.width / self.tileSize) / 2))
        startY = int(math.floor(self.centerY - (self.height / self.tileSize) / 2))
        endX = int(math.ceil(self.centerX + (self.width / self.tileSize) / 2))
        endY = int(math.ceil(self.centerY + (self.height / self.tileSize) / 2))
        self.offsetX = self.offsetX - math.floor((self.centerX - math.floor(self.centerX)) * self.tileSize)
        self.offsetY = -math.floor((self.centerY - math.floor(self.centerY)) * self.tileSize)
        self.offsetX += math.floor(self.width / 2)
        self.offsetY += math.floor(self.height / 2)
        self.offsetX += math.floor(startX - math.floor(self.centerX)) * self.tileSize
        self.offsetY += math.floor(startY - math.floor(self.centerY)) * self.tileSize
        for x in xrange(startX, endX + 1, 1):
            for y in xrange(startY, endY + 1, 1):
                url = self.tileSrcUrl[self.maptype]['url']
                url = url.replace('{Z}', str(self.zoom))
                url = url.replace('{X}', str(x))
                url = url.replace('{Y}', str(y))
                url = url.replace('{ABC}', random.choice('abc'))
                self.debug(url)
                tileData = self.fetchTile(url)
                if (tileData):
                    tempBuff = StringIO.StringIO()
                    tempBuff.write(tileData)
                    tempBuff.seek(0)
                    im = Image.open(tempBuff)
                else:
                    im = Image.open(self.errImg)
                destX = int((x - startX) * self.tileSize + self.offsetX)
                destY = int((y - startY) * self.tileSize + self.offsetY)
                self.image.paste(im, (destX, destY))

    def placeMarkers(self):
        """
            // loop thru marker array
        foreach ($this->markers as $marker) {
            // set some local variables
            $markerLat = $marker['lat'];
            $markerLon = $marker['lon'];
            $markerType = $marker['type'];
            // clear variables from previous loops
            $markerFilename = '';
            $markerShadow = '';
            $matches = false;
            // check for marker type, get settings from markerPrototypes
            if ($markerType) {
                foreach ($this->markerPrototypes as $markerPrototype) {
                    if (preg_match($markerPrototype['regex'], $markerType, $matches)) {
                        $markerFilename = $matches[0] . $markerPrototype['extension'];
                        if ($markerPrototype['offsetImage']) {
                            list($markerImageOffsetX, $markerImageOffsetY) = explode(",", $markerPrototype['offsetImage']);
                        }
                        $markerShadow = $markerPrototype['shadow'];
                        if ($markerShadow) {
                            list($markerShadowOffsetX, $markerShadowOffsetY) = explode(",", $markerPrototype['offsetShadow']);
                        }
                    }
                }
            }
            // check required files or set default
            if ($markerFilename == '' || !file_exists($this->markerBaseDir . '/' . $markerFilename)) {
                $markerIndex++;
                $markerFilename = 'lightblue' . $markerIndex . '.png';
                $markerImageOffsetX = 0;
                $markerImageOffsetY = -19;
            }
            // create img resource
            if (file_exists($this->markerBaseDir . '/' . $markerFilename)) {
                $markerImg = imagecreatefrompng($this->markerBaseDir . '/' . $markerFilename);
            } else {
                $markerImg = imagecreatefrompng($this->markerBaseDir . '/lightblue1.png');
            }
            // check for shadow + create shadow recource
            if ($markerShadow && file_exists($this->markerBaseDir . '/' . $markerShadow)) {
                $markerShadowImg = imagecreatefrompng($this->markerBaseDir . '/' . $markerShadow);
            }
            // calc position
            $destX = floor(($this->width / 2) - $this->tileSize * ($this->centerX - $this->lonToTile($markerLon, $this->zoom)));
            $destY = floor(($this->height / 2) - $this->tileSize * ($this->centerY - $this->latToTile($markerLat, $this->zoom)));
            // copy shadow on basemap
            if ($markerShadow && $markerShadowImg) {
                imagecopy($this->image, $markerShadowImg, $destX + intval($markerShadowOffsetX), $destY + intval($markerShadowOffsetY),
                    0, 0, imagesx($markerShadowImg), imagesy($markerShadowImg));
            }
            // copy marker on basemap above shadow
            imagecopy($this->image, $markerImg, $destX + intval($markerImageOffsetX), $destY + intval($markerImageOffsetY),
                0, 0, imagesx($markerImg), imagesy($markerImg));
        };
        :return:
        """
        # loop thru marker array
        self.debug(str(self.markers))
        for marker in self.markers:
            # // set some local variables
            markerLat = marker.get('lat')
            markerLon = marker.get('lon')
            markerType = marker.get('type', False)
            # // clear variables from previous loops
            markerFilename = ""
            markerShadow = False
            matches = False
            self.debug(str(marker))
            if (markerType):
                for name, markerPrototype in self.markerPrototypes.iteritems():
                    self.debug(markerPrototype)
                    self.debug('markerType:' + str(markerType))
                    regex = re.compile(markerPrototype['regex'], 0)
                    try:
                        matches = re.match(markerPrototype['regex'], markerType, re.IGNORECASE)
                    except:
                        self.debug('Wrong marker ')
                        continue
                    markerImageOffsetX = 0
                    markerImageOffsetY = 0
                    if (matches):
                        self.debug('matches.group(0):' + str(matches.group(0)))
                        markerFilename = matches.group(0) + markerPrototype['extension']

                        if markerPrototype['offsetImage']:
                            markerImageOffsetX, markerImageOffsetY = markerPrototype['offsetImage'].split(',', 2)
                            markerImageOffsetX, markerImageOffsetY = int(markerImageOffsetX), int(markerImageOffsetY)
                        markerShadow = markerPrototype['shadow']
                        if markerShadow:
                            markerShadowOffsetX, markerShadowOffsetY = markerPrototype['offsetShadow'].split(',', 2)
                            markerShadowOffsetX, markerShadowOffsetY = int(markerShadowOffsetX), int(markerShadowOffsetY)
            fullfilename = os.path.join(self.markerBaseDir, markerFilename)
            # // create img resource
            self.debug(fullfilename)
            if not os.path.exists(fullfilename) or os.path.isdir(fullfilename):
                fullfilename = os.path.join(self.markerBaseDir, 'lightblue1.png')
                markerImageOffsetX = 0
                markerImageOffsetY = -19
            self.debug(fullfilename)
            markerImg = Image.open(fullfilename).convert('RGBA')
            # // check for shadow + create shadow recource
            if markerShadow:
                 fullshadowfilename = os.path.join(self.markerBaseDir, markerShadow)
                 if os.path.exists(fullshadowfilename) and not os.path.isdir(fullshadowfilename) and markerShadow:
                     try:
                         markerShadowImg = Image.open(fullshadowfilename).convert('RGBA')
                     except:
                         # Забить если не тень не загрузилась
                         self.debug('Shadow load problem')

            (destY, destX) = self.coordsToPix(markerLat,markerLon)
            self.debug('destY:'+str(destY))
            self.debug('destX:'+str(destX))
            if (markerShadow and markerShadowImg):
                self.image.paste( markerShadowImg, (destX+markerShadowOffsetX, destY+markerShadowOffsetY),markerShadowImg)
            self.image.paste( markerImg, (destX+markerImageOffsetX, destY+markerImageOffsetY),markerImg)


    def tileUrlToFilename(self, url):
        url = url.replace('http://', '')
        url = url.replace('https://', '')
        return self.tileCacheBaseDir + "/" + url

    def checkTileCache(self, url):
        filename = self.tileUrlToFilename(url)
        if os.path.exists(filename):
            return open(filename).read()

    def checkMapCache(self):
        self.mapCacheID = hashlib.md5(self.serializeParams()).hexdigest()
        filename = self.mapCacheIDToFilename()
        if (os.path.exists(filename)):
            return True

    def serializeParams(self):
        return "&".join(
            [str(self.zoom), str(self.lat), str(self.lon), str(self.width), str(self.height), str(self.markers),
             self.maptype])

    def mapCacheIDToFilename(self):
        if not self.mapCacheFile:
            self.mapCacheFile = self.mapCacheBaseDir + "/" + self.maptype + "/" + str(self.zoom) + \
                                "/cache_" + self.mapCacheID[0: 2] + "/" + self.mapCacheID[2:2] + "/" + self.mapCacheID[
                                                                                                       4:]
        return self.mapCacheFile + "." + self.mapCacheExtension

    def mkdir_recursive(self, pathname, mode=0o777):
        try:
            os.makedirs(pathname, mode)
        except:
            pass

    def writeTileToCache(self, url, data):
        filename = self.tileUrlToFilename(url)
        path = os.path.dirname(filename.rstrip(os.pathsep)) or '.'
        self.mkdir_recursive(path)
        f = open(filename, 'w')
        f.write(data)
        f.close()

    def fetchTile(self, url):
        cached = self.checkTileCache(url)
        if (self.useTileCache and cached):
            return cached
        # Load from network
        if url.startswith('https://'):
            gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            req = urllib2.urlopen(url, context=gcontext)
        else:
            req = urllib2.urlopen(url)
        tile = req.read()
        if (tile and self.useTileCache):
            self.writeTileToCache(url, tile)
        return tile

    def copyrightNotice(self):
        draw = ImageDraw.Draw(self.image)
        font = ImageFont.truetype(self.font, self.fontSize)
        width, height = self.image.size

        draw.text((5, height - self.fontSize - 5), self.tileSrcUrl[self.maptype]['copyright'], self.fontColor,
                  font=font)
        """
        logoImg = Image.open(self.osmLogo).convert('RGBA')
        osmlogo_width, osmlogo_height = logoImg.size
        width, height = self.image.size
        destX = width - osmlogo_width
        destY = height - osmlogo_height
        self.image.paste(logoImg, (destX, destY))
        """

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

    def showMap(self, params):
        """
        :return : path to cached image of map
        """
        self.parseParams(params)
        if self.useMapCache:
            # use map cache, so check cache for map
            if not self.checkMapCache():
                # // map is not in cache, needs to be build
                self.makeMap()
                path = os.path.dirname(self.mapCacheIDToFilename().rstrip(os.pathsep)) or '.'
                self.mkdir_recursive(path)
                self.sendHeader()
                if os.path.exists(self.mapCacheIDToFilename()):
                    # return open(self.mapCacheIDToFilename(),'r').read()
                    return self.mapCacheIDToFilename()
                else:
                    self.image.save(self.mapCacheIDToFilename())
                    return self.mapCacheIDToFilename()
            else:
                # // map is in cache
                self.sendHeader()
                data = open(self.mapCacheIDToFilename(), 'r').read()
                # return data
                return self.mapCacheIDToFilename()
        else:
            # // no cache, make map, send headers and deliver png
            self.makeMap()
            self.sendHeader()
            # return imagepng($this->image);
            return self.mapCacheIDToFilename()


if __name__ == "__main__":
    params = {
        'center': '56.835640,60.005951',
        'zoom': '15',
        'size': '2048x2048',
        'maptype': 'opentopomap',
        'markers': '56.835640,60.005951,bullseye|56.834750,60.003941,lightblue2|56.836720,60.006531,lightblue3'
    }
    map = staticMapLite()
    print map.showMap(params)
