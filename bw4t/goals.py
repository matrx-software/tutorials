import itertools

from matrx import WorldBuilder
from matrx.goals import WorldGoal
from matrx.grid_world import GridWorld
from matrx.world_builder import RandomProperty


class CollectionGoal(WorldGoal):

    def __init__(self, name, target_name, in_order=False):
        super().__init__()
        # Store the attributes
        self.__area_name = name
        self.__target_name = target_name
        self.__in_order = in_order

        # Set attributes we will use to speed up things and keep track of collected objects
        self.__drop_off_locs = None  # all locations where objects can be dropped off
        self.__target_obj = None  # all (ordered) objects that need to be collected described in their properties
        self.__dropped_objects = {}  # a dictionary of the required dropped objects (id as key, tick as value)
        self.__progress = 0  # We also track the progress

    def goal_reached(self, grid_world: GridWorld):
        if self.__drop_off_locs is None:  # find all drop off locations, its tile ID's and goal blocks
            self.__drop_off_locs = []
            self.__find_drop_off_locations(grid_world)

        if self.__target_obj is None:  # find all objects that need to be collected (potentially in order)
            self.__target_obj = []
            self.__find_drop_off_locations(grid_world)

        # Go all drop locations and check if the requested objects are there (potentially dropped in the right order)
        is_satisfied, progress = self.__check_completion(grid_world)
        self.is_done = is_satisfied
        self.__progress = progress

        return is_satisfied

    def __find_drop_off_locations(self, grid_world):
        all_objs = grid_world.environment_objects
        for obj_id, obj in all_objs.items():
            if self.__area_name == obj.properties['name']:
                loc = obj.location.copy()
                self.__drop_off_locs.append(loc)

    def __find_collection_objects(self, grid_world):
        all_objs = grid_world.environment_objects
        for obj_id, obj in all_objs.items():
            if self.__area_name == obj.properties['collection_zone_name']:
                self.__target_obj = obj.properties['collection_objects'].copy()

    def __check_completion(self, grid_world):
        # Get the current tick number
        curr_tick = grid_world.current_nr_ticks

        # Retrieve all objects and the drop locations (this is the most performance heavy; it loops over all drop locs
        # and queries the world to locate all objects at that point through distance calculation. Note: this calculation
        # is not required, as the range is zero!).
        all_objs = grid_world.environment_objects
        obj_ids = [obj.obj_id for loc in self.__drop_off_locs
                   for obj in grid_world.get_objects_in_range(loc, sense_range=0)]

        # Go through all objects at the drop off locations. If an object was not already detected before as a
        # required object, check if it is one of the desired objects.
        detected_objs = {}
        for obj_id in obj_ids:
            obj_props = all_objs[obj_id].properties
            for req_props in self.__target_obj:
                if req_props <= obj_props:
                    detected_objs[obj_id] = curr_tick

        # Now compare the detected objects with the previous detected objects to see if any new objects were detected
        # and thus should be added to the dropped objects
        for obj_id in detected_objs.keys():
            if obj_id not in self.__dropped_objects.keys():
                self.__dropped_objects[obj_id] = detected_objs[obj_id]

        # Check if any objects detected previously are now not detected anymore, as such they need to be removed.
        removed = []
        for obj_id in self.__dropped_objects.keys():
            if obj_id not in detected_objs.keys():
                removed.append(obj_id)
        for obj_id in removed:
            self.__dropped_objects.pop(obj_id, None)

        # If required, check if the dropped objects are dropped in order by tracking the rank up which the dropped
        # objects satisfy the requested order.
        if self.__in_order:
            # Sort the dropped objects based on the tick they were detected (in ascending order)
            sorted_dropped_obj = sorted(self.__dropped_objects.items(), key=lambda x: x[1], reverse=False)
            rank = 0
            for obj_id, tick in sorted_dropped_obj:
                props = all_objs[obj_id]
                req_props = self.__target_obj[rank]
                if req_props <= props:
                    rank += 1
                else:
                    # as soon as the next object is not the one we expect, we stop the search at this attained rank.
                    break

            # Progress is the currently attained rank divided by the number of requested objects
            progress = rank / len(self.__target_obj)
            # The goal is done as soon as the attained rank is equal to the number of requested objects
            is_satisfied = rank == len(self.__target_obj)

        else:  # objects do not need to be collected in order
            # Progress the is the number of collected objects divided by the total number of requested objects
            progress = len(self.__dropped_objects) / len(self.__target_obj)
            # The goal is done when the number of collected objects equal the number of requested objects
            is_satisfied = len(self.__dropped_objects) == len(self.__target_obj)

        return is_satisfied, progress

    @classmethod
    def get_random_order_property(cls, possibilities, length=None, with_duplicates=False):
        if length is None:
            length = len(possibilities)

        if not with_duplicates:
            orders = itertools.permutations(possibilities, r=length)
        else:  # with_duplicates
            orders = itertools.product(possibilities, repeat=length)
        orders = list(orders)[0]

        rp_orders = RandomProperty(values=orders)

        return rp_orders


