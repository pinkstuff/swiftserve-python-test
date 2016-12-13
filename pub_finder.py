#!/usr/bin/python

import csv
import math
import sys
import logging
import argparse

logger = logging.getLogger(__name__)

class PostcodeLookupFailed(Exception):
    """Postcode lookup has failed exception"""
    pass

class Location(object):
    """Location class defines a location object"""
    
    def __init__(self, kwargs):
        """Constructor for location object takes argument
        kwargs which is a CSV dict iterator object. Contains
        the following atributes:
        postcode - postcode string
        east, north - Distance from 'origin' in meters
                      latitude, longitude are longitude and latitude 
                      coordinates in degrees"""

        self.postcode = kwargs["postcode"]
        self.east = float(kwargs["east"])
        self.north = float(kwargs["north"])
        self.latitude = kwargs["latitude"]
        self.longitude = kwargs["longitude"]

    @classmethod
    def lookup_coords(cls, postcode, filepath):
        """looks up postcode in postcode CSV file and returns
        an instantiated location object, takes postcode string and 
        filepath of postcode CSV file"""
        cls.filepath = filepath
        cls.fields = ("postcode", "east", "north", "latitude", "longitude")
        
        with open(filepath, "r") as postcode_file:
            postcode_reader = csv.DictReader(postcode_file, fieldnames=cls.fields)
            for entry in postcode_reader:
                # look for postcode in file NOT in memory
                # Make postcode lowercase and one word to avoid case
                # and formatting mistakes
                postcode_from_file = entry["postcode"].lower().replace(" ","")
                postcode_from_user = postcode.lower().replace(" ","")
                if  postcode_from_file == postcode_from_user:
                    logger.debug("Found {}".format(postcode))
                    return cls(entry)
            raise PostcodeLookupFailed()

    def __repr__(self):
        """Represent a location object by it lat/log coords"""
        return (self.latitude, self.longitude)

    def distance_from(self, location_obj):
        """finds distance between two points assuming a cartesian grid
        takes another location object and returns distance in km"""
        
        distance = math.sqrt(  (self.east - location_obj.east) ** 2 +
                               (self.north - location_obj.north) ** 2 )
        return distance / 1000.0


class Pub(object):
    """Class for creating Pub objects"""
    
    def __init__(self, name, location):
        """Constructor for Pub objects, has the following attributes:
        name - string of pubs name
        location - location object"""
      
        self.name = name
        self.location = location

    @classmethod
    def lookup_pubs(cls, pub_csv, postcode_csv):
        """looks up pub in Pub CSV file and generates
        an instantiated Pub object containing a location
        object. Takes the filepath of the pub CSV file.
        Can pass list of dictionaries for testing"""

        if type(pub_csv) is str:
            # Source is filepath to Pub CSV file
            cls.filepath = pub_csv
            cls.fields = ("name", "postcode")
           
            with open(cls.filepath, "r") as pub_address_file:
                pub_reader = csv.DictReader(pub_address_file, fieldnames=cls.fields)
                for entry in pub_reader:
                    # Can we find a Postcode entry?
                    try:
                        location_obj = Location.lookup_coords(
                                       entry["postcode"],
                                       postcode_csv)
                        # Got it, yield instance of Pub
                        yield cls(entry["name"], location_obj)
                    
                    except PostcodeLookupFailed:
                        msg = "Pub Postcode lookup failed {} - {}"
                        logger.info(msg.format(entry["name"], entry["postcode"]))
                   
        elif type(pub_csv) is list:
            # Use list of pubnames and location objects
            # useful for testing
            for name, location in pub_csv:
                yield cls(name, location)

        else:
            # Not sure whats going on,
            # Bailout
            raise TypeError


    def __repr__(self):
        """Represent a Pub object by its name"""
        return self.name
        
    @staticmethod
    def find_pubs(pub_csv, postcode_csv, 
                  current_location, max_return=20, max_distance=50):
        """Takes current location object. Then lookup all pubs 
        in pub CSV file computing the distance from current location. 
        Return  max_return number of pubs less than max distance"""
    
        list_of_pubs = []
        for pub in Pub.lookup_pubs(pub_csv, postcode_csv):
            # Compute distance
            distance = pub.location.distance_from(current_location)
            if distance < max_distance:
                # Are we in range?
                if len(list_of_pubs) < max_return:
                    # How much stuff do we want print?
                    list_of_pubs.append((pub.name, distance))
                    list_of_pubs = sorted(list_of_pubs, key=lambda x:x[1])
                
                elif distance < list_of_pubs[-1][1]:
                    # is distance smaller than last entry?
                    # we can save a sort if not
                    list_of_pubs.append((pub.name, distance))
                    list_of_pubs = sorted(list_of_pubs, key=lambda x:x[1])[:-1]
            
        return list_of_pubs



def parse_arguments():
    """Parse command line arguments and display help message"""
    
    parser = argparse.ArgumentParser()
    parser.add_argument("postcode", type=str, help="Postcode of current location")
    parser.add_argument("-d", "--debug", 
                         help="Turns on debug mode", 
                         action='store_true')
    parser.add_argument("-fp","--postcode-file", 
                         default="postcodes_swift_sample.csv",
                         help="Location of Postcode CSV file (default postcodes_swift_sample.csv)",
                         type=str)
    parser.add_argument("-fb","--pub-file", 
                         default="pubnames_swift_sample.csv",
                         help="Location of Pub Postcode CSV file (default pubnames_swift_sample.csv)",
                         type=str)
    parser.add_argument("-l","--limit", 
                         default=10, 
                         help="Limit Number of Results (default 10)",
                         type=int)
    parser.add_argument("-m","--max-distance", 
                         default=50, 
                         help="Only return results less than this distance (default 50)",
                         type=int)
    return parser


def main():
    """main entry point"""
    global args
    parser = parse_arguments()
    args = parser.parse_args()
    if args.debug: 
        logging.basicConfig(level=logging.DEBUG)

    try:
        # Is the postcode in the postcode file?
        whereami = Location.lookup_coords(args.postcode,
                                          args.postcode_file)
    except PostcodeLookupFailed:
        logger.error("Cant find current location")
        # Cant find postcode, we are all doomed
        return 1
    except FileNotFoundError:
        logger.error("Postcode file doesnt exist: {}".format(args.postcode_file))
        return 1

    try:
        results = Pub.find_pubs(args.pub_file, args.postcode_file, 
                                whereami, args.limit, args.max_distance)
    except FileNotFoundError:
        logger.error("Pub postcode file doesnt exist: {}".format(args.pub_file))
        return 1
    
    if len(results) == 0: 
        print("Sorry, this search didnt return any results") 
        print("Try increasing max distance")
        return 0
    for name, distance in results:
        print("{}  -  {} km".format(name, round(distance, 2)))
    return 0



if __name__ == "__main__":
    sys.exit(main())
