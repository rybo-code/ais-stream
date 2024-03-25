import asyncio
import websockets
import json
from dotenv import load_dotenv
import os
import argparse
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)

load_dotenv("../key/ais-stream.env")
api_key = os.getenv("API_KEY")


def write_json_to_file(data, file_path):
    with open(file_path, "a") as file:
        json.dump(data, file)
        file.write("\n")


async def connect_ais_stream_mmsi(args):
    num_messages = 0

    if "," in args.mmsi:
        mmsis = args.mmsi.split(",")
        mmsis = [i.strip() for i in mmsis]
        logging.info(f"searching mmsis:{mmsis}")
    else:
        mmsis = [args.mmsi]

    async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
        subscribe_message = {
            "APIKey": api_key,  # Required !
            "BoundingBoxes": [[[-90, -180], [90, 180]]],  # Required!
            "FiltersShipMMSI": mmsis,  # Optional!
        }
        if args.position == True:
            subscribe_message["FilterMessageTypes"] = ["PositionReport"]

        subscribe_message_json = json.dumps(subscribe_message)
        await websocket.send(subscribe_message_json)

        async for message_json in websocket:

            message = json.loads(message_json)

            if not "error" in message.keys():
                write_json_to_file(message, f"{args.outpath}.json")
                num_messages += 1
                logging.info(f"Processed {num_messages} message(s).")

                if num_messages >= args.limit:
                    break  # Break out of the loop
            else:
                logging.warning(message["error"])


async def connect_ais_stream_geofence(args):
    num_messages = 0
    # NOTE websocket subscription takes [lat,lon,lat,lon] so x and y values are inverted. Maybe??
    bbox = [args.y1, args.x1], [args.y2, args.x2]

    logging.info(f"searching bbox:{bbox}")

    async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
        # Initialize tqdm progress bar

        subscribe_message = {
            "APIKey": api_key,
            "BoundingBoxes": [bbox],
        }
        if args.position == True:
            subscribe_message["FilterMessageTypes"] = ["PositionReport"]

        subscribe_message_json = json.dumps(subscribe_message)
        await websocket.send(subscribe_message_json)
        logging.info(f"Subscribed to websocket. Listening...")
        pbar = tqdm(desc="Records received", unit=" records")
        async for message_json in websocket:

            # Update tqdm progress bar
            pbar.update(1)

            message = json.loads(message_json)

            if not "error" in message.keys():
                write_json_to_file(
                    message,
                    f"{args.outpath}\data.json",
                )
                num_messages += 1

                if num_messages >= args.limit:
                    break  # Break out of the loop

            else:
                logging.warning(message["error"])
    pbar.close()


async def main(args):
    # Collect the AIS messages

    if args.mmsi:
        # args.file_out_path = f"{args.outpath}/data"
        await connect_ais_stream_mmsi(args)  # Ensure the coroutine is awaited
    elif args.geofence:
        # file_out_path = f"{args.outpath}/data"
        await connect_ais_stream_geofence(args)

    print(f"Downloaded json data to {args.outpath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Listen for AIS from aisstream.io")

    parser.add_argument(
        "--mmsi",
        type=str,
        default=None,
        required=False,
        help="mmsi to track",
    )
    parser.add_argument(
        "--geofence",
        type=bool,
        default=False,
        required=False,
        help="mmsi to track",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        required=False,
        help="Max num msgs to wait for",
    )

    parser.add_argument(
        "--outpath",
        type=str,
        default="./ais_data",
        help="Output filepath",
    )

    parser.add_argument(
        "--x1",
        type=float,
        default="-90",
        help="Bounding box longitude 1",
    )
    parser.add_argument(
        "--y1",
        type=float,
        default="180",
        help="Bounding box latitude 1",
    )
    parser.add_argument(
        "--x2",
        type=float,
        default="90",
        help="Bounding box longitude 2",
    )
    parser.add_argument(
        "--y2",
        type=float,
        default="-180",
        help="Bounding box latitude 1",
    )
    parser.add_argument(
        "--env",
        type=str,
        default="../env/ais-stream.env",
        help="Path to your env file",
    )

    parser.add_argument(
        "--position",
        type=bool,
        default="True",
        help="Msg type to download",
    )
    args = parser.parse_args()
    asyncio.run(main(args))  # Pass the coroutine object to asyncio.run()
