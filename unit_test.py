#!/usr/bin/python 
import unittest 
from pub_finder import *
import logging

logger = logging.getLogger(__name__)

class PubFinderTestCase(unittest.TestCase):
      
    def setUp(self):
    
        self.list_of_points = []
        self.current_location = { "postcode" : "ST10 1UF",
                                  "east" : "500000",
                                  "north" : "500000",
                                  "latitude" : "52.976801",
                                  "longitude" : "-2.004769"} 
        self.points = [(2,5), (5.5,5.5), (5,4), (7,5), (7,7)]

        self.dict_template = { "postcode" : "ST10 1UF",
                               "east" : "399777",
                               "north" : "342161",
                               "latitude" : "52.976801",
                               "longitude" : "-2.004769"} 

        for x,y in self.points: 
            location = self.dict_template.copy()
            location.update( { "east" : str( x * 100000 ), 
                               "north" : str( y * 100000) } )
            self.list_of_points.append( location )

        
    def test_distance_between(self):
        current_location = Location(self.current_location) 
        target_location = Location(self.list_of_points[0])
        distance = target_location.distance_from(current_location)
        self.assertEqual(300.0, distance)


    def test_pub_order(self):
        current_location = Location(self.current_location) 
        pubs = [] 
        for number, entry in enumerate(self.list_of_points): 
            location_obj = Location(entry)
                           
            pubs.append(("Pub{}".format(number), location_obj))

        results = Pub.find_pubs(pubs, None, current_location, max_distance=1000)
        for code, actual in zip(results, (("Pub1",70.71), ("Pub2", 100.0), ("Pub3", 200.0),("Pub4", 282.84), ("Pub0",300.00))):
            rounded = (code[0], round(code[1], 2))
            self.assertEqual(rounded, actual)

    def test_no_of_results(self):
        current_location = Location(self.current_location) 
        pubs = [] 
        for number, entry in enumerate(self.list_of_points): 
            location_obj = Location(entry)
                           
            pubs.append(("Pub{}".format(number), location_obj))

        results = Pub.find_pubs(pubs, None, current_location,max_return=3, max_distance=1000)
        self.assertEqual(len(results), 3)
    
    def test_bad_postcode_filename(self):
        current_location = Location(self.current_location) 
        pubs = [] 
        for number, entry in enumerate(self.list_of_points): 
            location_obj = Location(entry)
                           
            pubs.append(("Pub{}".format(number), location_obj))

        self.assertRaises(FileNotFoundError, 
                          Pub.find_pubs,
                          "/path/does/not/exist", 
                          current_location, 5)

    def test_bad_pub_filename(self):
        self.assertRaises(FileNotFoundError, 
                          Location.lookup_coords,
                          "CB5 8PF", 
                          "/path/does/not/exist")

if __name__ == "__main__":
    unittest.main()
