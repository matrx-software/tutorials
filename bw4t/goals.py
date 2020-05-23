import itertools
import warnings

from matrx import WorldBuilder
from matrx.goals import WorldGoal
from matrx.grid_world import GridWorld
from matrx.world_builder import RandomProperty
from bw4t.objects import CollectionTarget, CollectionDropOffTile


class CollectionGoal(WorldGoal):

    def __init__(self, name, target_name, in_order=False):
        super().__init__()
        # Store the attributes
        self.__area_name = name
        self.__target_name = target_name
        self.__in_order = in_order

        # Set attributes we will use to speed up things and keep track of collected objects
        self.__drop_off_locs = None  # all locations where objects can be dropped off
        self.__target = None  # all (ordered) objects that need to be collected described in their properties
        self.__dropped_objects = {}  # a dictionary of the required dropped objects (id as key, tick as value)
        self.__attained_rank = 0  # The maximum attained rank of the correctly collected objects (only used if in_order)

    def goal_reached(self, grid_world: GridWorld):
        if self.__drop_off_locs is None:  # find all drop off locations, its tile ID's and goal blocks
            self.__drop_off_locs = []
            self.__find_drop_off_locations(grid_world)
            # Raise exception if no drop off locations were found.
            if len(self.__drop_off_locs) == 0:
                raise ValueError(f"The CollectionGoal {self.__area_name} could not find a "
                                 f"{CollectionDropOffTile.__name__} with its 'collection_area_name' set to "
                                 f"{self.__area_name}.")

        if self.__target is None:  # find all objects that need to be collected (potentially in order)
            self.__target = []
            self.__find_collection_objects(grid_world)

        # Go all drop locations and check if the requested objects are there (potentially dropped in the right order)
        is_satisfied = self.__check_completion(grid_world)
        self.is_done = is_satisfied

        return is_satisfied

    def __find_drop_off_locations(self, grid_world):
        all_objs = grid_world.environment_objects
        for obj_id, obj in all_objs.items():
            if 'name' in obj.properties.keys() \
                    and self.__area_name == obj.properties['name']:
                loc = obj.location
                self.__drop_off_locs.append(loc)

    def __find_collection_objects(self, grid_world):
        all_objs = grid_world.environment_objects
        for obj_id, obj in all_objs.items():
            if 'collection_zone_name' in obj.properties.keys() \
                    and self.__area_name == obj.properties['collection_zone_name']\
                    and 'collection_objects' in obj.properties and 'is_drop_off_target' in obj.properties\
                    and obj.properties['is_drop_off_target']:
                self.__target = obj.properties['collection_objects'].copy()

        # Raise warning if no target object was found.
        if len(self.__target) == 0:
            warnings.warn(f"The CollectionGoal {self.__area_name} could not find a {CollectionTarget.__name__} "
                          f"object or its 'collection_objects' property is empty.")

    def __check_completion(self, grid_world):
        # If we were already done before, we return the past values
        if self.is_done:
            return self.is_done

        # Get the current tick number
        curr_tick = grid_world.current_nr_ticks

        # Retrieve all objects and the drop locations (this is the most performance heavy; it loops over all drop locs
        # and queries the world to locate all objects at that point through distance calculation. Note: this calculation
        # is not required, as the range is zero!).
        obj_ids = [obj_id for loc in self.__drop_off_locs
                   for obj_id in grid_world.get_objects_in_range(loc, sense_range=0, object_type=None).keys()]

        # Get all world objects and agents
        all_objs = grid_world.environment_objects
        all_agents = grid_world.registered_agents
        all_ = {**all_objs, **all_agents}

        # Go through all objects at the drop off locations. If an object was not already detected before as a
        # required object, check if it is one of the desired objects. Also, ignore all drop off tiles and targets.
        detected_objs = {}
        for obj_id in obj_ids:
            obj_props = all_[obj_id].properties
            # Check if the object is either a collection area tile or a collection target object, if so skip it
            if ("is_drop_off" in obj_props.keys() and "collection_area_name" in obj_props.keys()) \
                    or ("is_drop_off_target" in obj_props.keys() and "collection_zone_name" in obj_props.keys()
                        and "is_invisible" in obj_props.keys()):
                continue
            for req_props in self.__target:
                obj_props = CollectionGoal.__flatten_dict(obj_props)
                if req_props.items() <= obj_props.items():
                    detected_objs[obj_id] = curr_tick

        # Now compare the detected objects with the previous detected objects to see if any new objects were detected
        # and thus should be added to the dropped objects
        is_updated = False
        for obj_id in detected_objs.keys():
            if obj_id not in self.__dropped_objects.keys():
                is_updated = True
                self.__dropped_objects[obj_id] = detected_objs[obj_id]

        # Check if any objects detected previously are now not detected anymore, as such they need to be removed.
        removed = []
        for obj_id in self.__dropped_objects.keys():
            if obj_id not in detected_objs.keys():
                removed.append(obj_id)
        for obj_id in removed:
            is_updated = True
            self.__dropped_objects.pop(obj_id, None)

        # If required (and needed), check if the dropped objects are dropped in order by tracking the rank up which the
        # dropped objects satisfy the requested order.
        if self.__in_order and is_updated:
            # Sort the dropped objects based on the tick they were detected (in ascending order)
            sorted_dropped_obj = sorted(self.__dropped_objects.items(), key=lambda x: x[1], reverse=False)
            rank = 0
            for obj_id, tick in sorted_dropped_obj:
                props = all_[obj_id].properties
                props = CollectionGoal.__flatten_dict(props)
                req_props = self.__target[rank]
                if req_props.items() <= props.items():
                    rank += 1
                else:
                    # as soon as the next object is not the one we expect, we stop the search at this attained rank.
                    break

            # The goal is done as soon as the attained rank is equal to the number of requested objects
            is_satisfied = rank == len(self.__target)
            # Store the attained rank, used to measure the progress
            self.__attained_rank = rank

        # objects do not need to be collected in order and new ones were dropped
        elif is_updated:
            # The goal is done when the number of collected objects equal the number of requested objects
            is_satisfied = len(self.__dropped_objects) == len(self.__target)

        # no new objects detected, so just return the past values
        else:
            is_satisfied = self.is_done

        return is_satisfied

    def get_progress(self, grid_world):
        # If we are done, just return 1.0
        if self.is_done:
            return 1.0

        # Check if the order matters, if so calculated the progress based on the maximum attained rank of correct
        # ordered collected objects.
        if self.__in_order:
            # Progress is the currently attained rank divided by the number of requested objects
            progress = self.__attained_rank / len(self.__target)

        # If the order does not matter, just calculate the progress as the number of correctly collected/dropped
        # objects.
        else:
            # Progress the is the number of collected objects divided by the total number of requested objects
            progress = len(self.__dropped_objects) / len(self.__target)

        return progress

    @classmethod
    def get_random_order_property(cls, possibilities, length=None, with_duplicates=False):
        if length is None:
            length = len(possibilities)

        if not with_duplicates:
            orders = itertools.permutations(possibilities, r=length)
        else:  # with_duplicates
            orders = itertools.product(possibilities, repeat=length)
        orders = list(orders)

        rp_orders = RandomProperty(values=orders)

        return rp_orders


