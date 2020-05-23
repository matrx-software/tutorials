import copy
from collections import Iterable

from matrx.objects import Door, AreaTile, Wall

from bw4t.builder import _flatten_dict


class State:

    def __init__(self, memorize_for_ticks=None):
        if memorize_for_ticks is None:
            self.__decay_val = 0
        else:
            self.__decay_val = 1.0 / memorize_for_ticks

        self.__state_dict = {}
        self.__prev_state_dict = {}
        self.__decays = {}

    def update(self, state_dict):
        prev_state = self.__state_dict.copy()
        state = state_dict.copy()

        # Get the ids of all newly perceived objects
        new_ids = set(state.keys()) - set(prev_state.keys())

        # Get the ids of all objects that were perceived before as well
        persistent_ids = set(state.keys()) - new_ids

        # Get the ids of all objects that are not perceived any more
        gone_ids = set(prev_state.keys()) - set(state.keys())

        # Handle knowledge decay if decay actually matters (e.g. that stuff need to be memorized)
        if self.__decay_val > 0:
            # Decay the decays of all objects that are not perceived any longer
            for obj_id in gone_ids:
                self.__decays[obj_id] = max((self.__decays[obj_id] - self.__decay_val), 0)

            # Reset the decays of all objects that are still perceived
            for obj_id in persistent_ids:
                self.__decays[obj_id] = 1.0

            # Add all new decays of the newly perceived objects
            for obj_id in new_ids:
                self.__decays[obj_id] = 1.0

            # Check for non-zero decays and flag them for keeping (this now also includes all new_ids as we just added
            # them).
            to_keep_ids = []
            for obj_id, decay in self.__decays.items():
                if decay > 0:
                    to_keep_ids.append(obj_id)
                else:  # remove all zero decay objects, this reduces the self.__decays of growing with zero decays
                    self.__decays.pop(obj_id)
            to_keep_ids = set(to_keep_ids)

        # If decay does not matter, flag all objects for keeping that are newly or still perceived
        else:
            to_keep_ids = new_ids.union(persistent_ids)

        # Create new state
        new_state = {}
        for obj_id in to_keep_ids:
            # If the object id is in the received state, pick that one. This makes sure that any objects that were also
            # in the previous state get updated with newly perceived properties
            if obj_id in state.keys():
                new_state[obj_id] = state[obj_id]
            # If the object id is not in the received state, it may still be in the previous state (e.g. because its
            # decay was non-zero). Though this only happens when decay is set.
            elif obj_id in prev_state.keys():
                new_state[obj_id] = prev_state[obj_id]

        # Set the new state
        self.__prev_state_dict = self.__state_dict
        self.__state_dict = new_state

        # Return self
        return self

    ###############################################
    # Methods that allow State to be used as dict #
    ###############################################
    def __getitem__(self, obj_id):
        self.__find_object(prop_name=["obj_id", "name"], prop_value=obj_id)

    def __len__(self):
        return len(self.__state_dict)

    def copy(self):
        return copy.deepcopy(self)

    def pop(self, obj_id):
        return self.__state_dict.pop(obj_id)

    def remove(self, obj_id):
        self.__state_dict.pop(obj_id)

    def as_dict(self):
        return self.__state_dict

    ###############################################
    #     Some helpful getters for the state      #
    ###############################################
    def get_with_property(self, prop_name, prop_value=None):
        found = self.__find_object(prop_name, prop_value)
        return found

    def get_world_info(self):
        return self.__state_dict['World']

    def remove_with_property(self, prop_name, prop_value=None):
        found = self.__find_object(prop_name, prop_value)
        (self.remove(obj['obj_id']) for f in found for obj in f)

    def get_of_type(self, obj_type):
        return self.get_with_property("class_inheritance", obj_type)

    def get_room_objects(self, room_name):
        return self.get_with_property("name", room_name)

    def get_all_room_names(self):
        # TODO: Needs a way to identify rooms (e.g. with Doors/Walls/Tiles having a 'part_of_room' property for instance
        pass

    def get_room_content(self, room_name):
        # Locate method to identify room content
        def is_content(obj):
            if 'class_inheritance' in obj.keys():
                chain = obj['class_inheritance']
                if not (Wall.__name__ in chain or Door.__name__ in chain or AreaTile in chain):
                    return obj
            else:  # the object is a Wall, Door or AreaTile
                return None

        # Get all room objects
        room_objs = self.get_room_objects(room_name)

        # Filter out all area's, walls and doors
        content = map(is_content, room_objs)
        content = [c for c in content if c is not None]

        return content

    def get_room_doors(self, room_name):
        # Locate method to identify doors
        def is_content(obj):
            if 'class_inheritance' in obj.keys():
                chain = obj['class_inheritance']
                if Door.__name__ in chain:
                    return obj
            else:  # the object is not a Door
                return None

        room_objs = self.get_room_objects(room_name)
        # Filter out all doors
        doors = map(is_content, room_objs)
        doors = [c for c in doors if c is not None]

        return doors

    def get_agents(self):
        pass

    def get_agent_with_property(self, prop_name, prop_value):
        pass

    def get_team_members(self):
        pass

    def get_closest(self):
        pass

    def get_closest_with_property(self, prop_name, prop_value):
        pass

    def get_closest_room(self):
        pass

    def get_closest_agent(self):
        pass

    ###############################################
    # Some higher level abstractions of the state #
    ###############################################
    def get_traverse_map(self):
        pass

    def get_distance_map(self):
        pass

    def apply_occlusion(self):
        pass

    ##################################################
    # The basic functions that make up most of state #
    ##################################################
    def __find_object(self, prop_name, prop_value=None):

        # Make sure the property names and property values are iterables.
        names = prop_name.copy()
        if not isinstance(prop_name, Iterable):
            names = (prop_name, )
            prop_value = (prop_value, )

        # Check if the number of given property names match the number of given poperty values.
        if len(names) is not len(prop_value):
            raise ValueError(f"When searching for objects with properties {prop_name} and values {prop_value}, the "
                             f"number of given property values does not the number of given property names.")

        # For each prop_name, prop_value combination, find the relevant objects.
        found = [self.__find(name, val) for name, val in zip(prop_name, prop_value)]

        # If nothing was found, we set it to None for easy identification and break any iterable over it.
        if not found:
            found = None

        return found

    def __find(self, prop_name, prop_value=None):
        # A local function that identifies whether a given obj_id-obj pair has the requested property name and, if
        # given, the right property value. Is used in the map method to find all object that adhere to it.
        def locate(id_obj_pair):
            obj = id_obj_pair[1]

            # The object is found when it has the property and the value is none, or when it has the property and the
            # requested value is the value of that property OR is in that value of that property (e.g. as substring or
            # list item).
            if prop_name in obj:
                if prop_value is None or (prop_value == obj[prop_name] or prop_value in obj[prop_name]):
                    return obj
            return None

        # try to locate it in the regular dict as an object id, this allows us to use this method also to quickly locate
        # objects based on their object ID.
        try:
            return self.__state_dict[prop_value]

        # if the prop value was not a key in the dict (or simply None), find all objects with that property and value if
        # given. This uses Python's map function to bring our search to C.
        except KeyError:
            located = map(locate, self.__state_dict.items())
            return [l for l in located if l is not None]  # only return the found objects
