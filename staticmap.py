"""

"""


class staticMapLite:
    def __init__(self):
        self.maxWidth = 1024
        self.maxHeight = 1024
        self.tileSize = 256
        self.tileSrcUrl = {
            'mapnik': 'http://tile.openstreetmap.org/{Z}/{X}/{Y}.png',
            'osmarenderer': 'http://otile1.mqcdn.com/tiles/1.0.0/osm/{Z}/{X}/{Y}.png',
            'cycle': 'http://a.tile.opencyclemap.org/cycle/{Z}/{X}/{Y}.png',
        }
        self.tileDefaultSrc = 'mapnik'
        self.markerBaseDir = 'images/markers'
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
        self.tileCacheBaseDir = '../cache/tiles'
        self.useMapCache = True
        self.mapCacheBaseDir = '../cache/maps'
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

    def parseParams(params):
        if (params['show'] != ""):
            self.parseOjwParams(params)
        else:
            self.parseLiteParams(params)

    def parseLiteParams(params):
        # get zoom from GET paramter
        try:
            self.zoom = int(params['zoom'])
        except:
            self.zoom = 0
        self.zoom = 18 if self.zoom > 18
        if ($this->zoom > 18) $this->zoom = 18;
        // get lat and lon from GET paramter
        list($this->lat, $this->lon) = explode(',', $_GET['center']);
        $this->lat = floatval($this->lat);
        $this->lon = floatval($this->lon);
        // get size from GET paramter
        if ($_GET['size']) {
            list($this->width, $this->height) = explode('x', $_GET['size']);
            $this->width = intval($this->width);
            if ($this->width > $this->maxWidth) $this->width = $this->maxWidth;
            $this->height = intval($this->height);
            if ($this->height > $this->maxHeight) $this->height = $this->maxHeight;
        }
        if (!empty($_GET['markers'])) {
            $markers = explode('|', $_GET['markers']);
            foreach ($markers as $marker) {
                list($markerLat, $markerLon, $markerType) = explode(',', $marker);
                $markerLat = floatval($markerLat);
                $markerLon = floatval($markerLon);
                $markerType = basename($markerType);
                $this->markers[] = array('lat' => $markerLat, 'lon' => $markerLon, 'type' => $markerType);
            }
        }
        if ($_GET['maptype']) {
            if (array_key_exists($_GET['maptype'], $this->tileSrcUrl)) $this->maptype = $_GET['maptype'];
        }

if __name__ == "__main__":
    params = {
        'center': '40.714728,-73.998672',
        'zoom': '14',
        'size': '512x512',
        'maptype': 'mapnik',
        'markers': '40.702147,-74.015794,blues|40.711614,-74.012318,greeng|40.718217,-73.998284,redc'
    }
    map = staticMapLite()
    map.showMap()
