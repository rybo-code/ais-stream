import argparse
import json
import pandas as pd


def write_csv_to_file(data, file_path):
    position_msgs = ["PositionReport", "StandardClassBPositionReport"]
    # Read JSON lines directly into a DataFrame
    df = pd.concat([pd.json_normalize(data)], ignore_index=True)
    df = df.query("MessageType in @position_msgs")

    # Explode the DataFrame to separate rows for each nested field
    df_exploded = df.apply(lambda x: x.explode() if x.dtype == "O" else x)
    df_exploded.to_csv(file_path + ".csv", index=False)

    return


def write_json_to_file(data, file_path):
    with open(file_path, "a") as file:
        json.dump(data, file)
        file.write("\n")


def write_geojson_to_file(data, output_path, incl_polyline=False):

    msgs_geojson = transform_to_geojson(data, incl_polyline)
    write_json_to_file(msgs_geojson, output_path)
    return


def transform_to_geojson(json_data, incl_polyline):
    """Transform a POSITION type message to geo"""

    geojson_features = list()
    all_coordinates = dict()
    all_mmsis = set()

    for message_data in json_data:
        # Only process the position data
        if message_data["MessageType"] == "PositionReport":
            position_report = message_data["Message"]["PositionReport"]
            metadata = message_data["MetaData"]

            mmsi = position_report["UserID"]
            ship_name = metadata["ShipName"]
            latitude = position_report["Latitude"]
            longitude = position_report["Longitude"]
            speed = position_report["Sog"]
            all_mmsis.add(mmsi)
            mmsi_coords = all_coordinates.get(mmsi, [])

            # Append coords to the list
            mmsi_coords.append([longitude, latitude])
            all_coordinates[mmsi] = mmsi_coords

            feature = {
                "type": "Feature",
                "properties": {"MMSI": mmsi, "ShipName": ship_name, "Speed": speed},
                "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
            }

            geojson_features.append(feature)
        else:
            continue

    if incl_polyline == True:
        for mmsi in all_mmsis:
            # Create a LineString geometry using all the collected coordinates
            line_geometry = {"type": "LineString", "coordinates": all_coordinates[mmsi]}

            # Create the polyline feature
            polyline_feature = {
                "type": "Feature",
                "properties": {"Type": "Polyline", "MMSI": mmsi},
                "geometry": line_geometry,
            }

            # Append the polyline feature to geojson_features
            geojson_features.append(polyline_feature)

    # Create the GeoJSON object
    geojson = {"type": "FeatureCollection", "features": geojson_features}

    return geojson


def main(args):
    json_file_path = args.inpath
    data = [json.loads(line) for line in open(json_file_path)]
    # Save the messages in geojson format as points and lines
    write_geojson_to_file(data, args.outpath + ".geojson", args.trackline)
    write_csv_to_file(data, args.outpath)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Listen for AIS from aisstream.io")

    parser.add_argument(
        "--inpath",
        type=str,
        default="./ais_data/data.json",
        help="Output filepath",
    )

    parser.add_argument(
        "--outpath",
        type=str,
        default="./ais_data/data",
        help="Output filepath",
    )

    parser.add_argument(
        "--trackline",
        type=bool,
        default=False,
        help="True/False produce vessel track line",
    )

    args = parser.parse_args()
    main(args)
