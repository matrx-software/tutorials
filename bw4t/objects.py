from collections import Iterable

from matrx.objects import AreaTile, EnvObject
import numpy as np


class CollectionTarget(EnvObject):
    def __init__(self, location, collection_objects, collection_zone_name, name="Collection_target"):
        """ An invisible object that tells which objects needs collection.

        This invisible object is linked to `CollectionDropTile` object(s) and is used by the `CollectionGoal` to
        identify which objects should be collected and dropped off at the tiles. This object is just a regular object
        but contains three additional properties:
        - collection_objects: See parameter doc.
        - collection_zone_name: See parameter doc.
        - is_invisible: A boolean denoting that this object is invisible. This boolean has no effect in MATRX, except to
        denote that this object is not an actual visible object.
        - is_drop_off_target: Denotes this object as containing the descriptions of the to be collected objects.

        The invisibility is implemented as a block with full opacity, not movable, fully traversable and always below
        other objects.

        Parameters
        ----------
        location : (x, y)
            The location of this object.
        collection_objects : List of dicts
            A list of dictionaries, each dictionary in this list represents an object that should be dropped at this
            location. The dictionary itself represents the property-value pairs these objects should adhere to. The
            order of the list matters iff the `CollectionGoal.in_order==True`, in which case the
            `CollectionGoal` will track if the dropped objects at this tile are indeed dropped in the order of the list.
        collection_zone_name : str
            This is the name that links `CollectionDropTile` object(s) to this object. The `CollectionGoal` will check
            all of these tiles with this name to check if all objects are already dropped and collected.
        name : str (default is "Collection_target")
            The name of this object.

        Notes
        -----
        It does not matter where this object is added in the world. However, it is good practice to add it on top of
        the (or one of them) `CollectionDropTile` object(s). The helper method to create collection areas
        `WorldBuilder.add_collection_goal` follows this practice.

        See Also
        --------
        matrx.WorldBuilder.add_collection_goal
                The handy method in the `WorldBuilder` to add a collection goal to the world and required object(s).
        matrx.goals.CollectionGoal
            The `CollectionGoal` that performs the logic of check that all object(s) are dropped at the drop off tiles.
        matrx.objects.CollectionDropTile
            The tile that represents the location(s) where the object(s) need to be dropped.
        """
        super().__init__(location=location, name=name, class_callable=CollectionTarget, customizable_properties=None,
                         is_traversable=True, is_movable=False, visualize_size=0, visualize_shape=0,
                         is_drop_off_target=True, visualize_colour=None, visualize_depth=None, visualize_opacity=0.0,
                         collection_objects=collection_objects, collection_zone_name=collection_zone_name,
                         is_invisible=True)


class CollectionDropOffTile(AreaTile):
    def __init__(self, location, name="Collection_zone", collection_area_name="Collection zone",
                 visualize_colour="#64a064", visualize_opacity=1.0, **kwargs):
        """
        An area tile used to denote where one or more objects should be dropped. It is similar to any other `AreaTile`
        but has two additional properties that identify it as a drop off location for objects and the name of the drop
        off. These are used by a `CollectionGoal` to help find the drop off area in all world objects.

        Parameters
        ----------
        location : (x, y)
            The location of this tile.
        name : str (default is "Collection_zone")
            The name of this tile.
        collection_area_name: str (default is "Collection_zone")
            The name of the collection zone this collection tile belongs to. It is used by the respective CollectionGoal
            to identify where certain objects should be dropped.
        visualize_colour : String (default is "#64a064", a pale green)
            The colour of this tile.
        visualize_opacity : Float (default is 1.0)
            The opacity of this tile. Should be between 0.0 and 1.0.

        See also
        --------
        matrx.WorldBuilder.add_collection_goal
                The handy method in the `WorldBuilder` to add a collection goal to the world and required object(s).
        matrx.goals.CollectionGoal
            The `CollectionGoal` that performs the logic of check that all object(s) are dropped at the drop off tiles.
        matrx.objects.CollectionTarget
            The invisible object representing which object(s) need to be collected and (if needed) in which order.
        """
        super().__init__(location, name=name, visualize_colour=visualize_colour, visualize_depth=None,
                         visualize_opacity=visualize_opacity, is_drop_off=True,
                         collection_area_name=collection_area_name, **kwargs)


# class GhostBlock(EnvObject):
#     def __init__(self, location, drop_zone_nr, name, visualize_colour, visualize_shape):
#         super().__init__(location, name, is_traversable=True, is_movable=False,
#                          visualize_colour=visualize_colour, visualize_shape=visualize_shape,
#                          visualize_size=block_size,
#                          visualize_depth=85, drop_zone_nr=drop_zone_nr, visualize_opacity=0.5,
#                          is_drop_zone=False, is_goal_block=True, is_collectable=False)

