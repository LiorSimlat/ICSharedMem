import multiprocessing
import os
import sys
from typing import Literal


def main():
    #import depndencies
    from affine import Affine
    import numpy as np
    import rasterio
    from rasterio.io import MemoryFile
    import socket
    import yaml
    from rasterio.env import Env

    #read config 
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    MCAST_GRP = config["multicast"]["group"]
    MCAST_PORT = config["multicast"]["port"]
    MAX_PACKET_SIZE = config["multicast"]["max_packet_size"]

    # Create a sample image (e.g. 3-band RGB 100x100)
    width, height, count = 200, 200, 3
    data = np.full((height, width, count), 255, dtype= np.uint8)
    data[height // 2 - 1: height//2 + 1, :] = 0
    data = data.transpose((2, 0, 1))

    profile = {
        'driver': 'JP2OpenJPEG',
        'dtype': 'uint8',
        'count': count,
        'height': height,
        'width': width,
        'crs': None,
        'transform': None,
        "compress": "JP2"
    }

    # Save the image as JPEG2000 to disk for verification
    with Env(GDAL_PAM_ENABLED="NO"):
        # Write image to a Rasterio MemoryFile as JPEG2000
        with MemoryFile() as memfile:
            with memfile.open(**profile) as dataset:
                dataset.write(data)
            
            # Get the JPEG2000 bytes
            jpeg2000_bytes = memfile.read()

    with open("output.jp2", "wb") as f:
        f.write(jpeg2000_bytes)

    padding_options = config.get("message_padding", [])
    print("Option: ", padding_options[0])  #one of -> ['around', 'before', 'after']
    def apply_padding(message_bytes: bytes, padding_option: Literal["around", "before", "after"]) -> bytes:
        dummy_byte = b'\x00'  # define dummy byte, can be anything

        padded = message_bytes

        if "around" == padding_option:
            # one dummy byte before and after
            padded = dummy_byte + padded + dummy_byte

        if "before" == padding_option:
            # two dummy bytes before
            padded = b'\x00\x00' + padded

        if "after" == padding_option:
            # two dummy bytes after
            padded = padded + b'\x00\x00'

        return padded

    print ("Before padding: ", len(jpeg2000_bytes))
    jpeg2000_bytes = apply_padding(jpeg2000_bytes, padding_options[0])
    print ("After padding: ", len(jpeg2000_bytes))
    # Create a UDP socket for multicast
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    # Send the data in chunks (max UDP packet size is ~65KB, often less in practice)
    #if MAX_PACKET_SIZE is -1 send all in once 
    if MAX_PACKET_SIZE != -1:
        for i in range(0, len(jpeg2000_bytes), MAX_PACKET_SIZE):
            chunk = jpeg2000_bytes[i:i+MAX_PACKET_SIZE]
            sock.sendto(chunk, (MCAST_GRP, MCAST_PORT))
    else:
        chunk = jpeg2000_bytes
        sock.sendto(chunk, (MCAST_GRP, MCAST_PORT))

if __name__ == "__main__":
    multiprocessing.freeze_support()
    # create element tree object
    if getattr(sys, 'frozen', False):
    # If the application is run as a bundle
        print ("bundle")
        bundle_dir = sys._MEIPASS
        print("Bundle directory:", bundle_dir)
    
        os.environ['PROJ_LIB'] = os.path.join(bundle_dir, 'rasterio', 'proj_data')  # Specific path for proj_data 
        #(Note: there are several installation of proj data directories. in rasterio , pyproj , fiona. they are diiferent installations. the code uses the rasterio library the most and there for the proj_dir of the rasterio library has been chosen )
        
        print ('PROJ_LIB', os.environ['PROJ_LIB'])  # Specific path for pyproj)

        os.environ['GDAL_DATA'] = os.path.join(bundle_dir, 'gdal_data')
        print ('GDAL_DATA', os.path.join(bundle_dir, 'gdal_data'))  # Specific path for pyproj)

    else:
        print ("dev")
    
    main()
