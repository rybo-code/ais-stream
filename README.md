
## Usage/Examples

#### Download AIS data to JSON format
Subscribe to AIS messages for a single MMSI, limited to the first 100 messages received.  
**Note:** Rate limiting not yet implemented, websocket may close if too many messages are pending. To avoid keep limit < 10,000 messages
```bash
python ./src/ais-stream.py --outpath ./ais_data --geofence False --mmsi 235112742 --limit 100
```

Subscribe to AIS messages in a defined area. Input x (longitude) and y(latitude) values for two coordinates defining the top left and bottom right corners of a bounding box. Defaults to entire world -90,180 and 90,-180.

```bash
python src/ais-streaming.py --geofence True --x1 -90 --y1 180 --x2 90 --y2 -180 --limit 100
```

#### Format downloaded data to GeoJSON and CSV for analysis

```bash
python ./src/ais-format.py --infile ./ais_data/data.json --outpath ./ais_data
```