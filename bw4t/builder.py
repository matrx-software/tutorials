# The methods and classes below can be added to the WorldBuilder
from matrx.goals import WorldGoal, LimitedTimeGoal
from matrx.world_builder import RandomProperty

from bw4t.goals import CollectionGoal
from bw4t.objects import CollectionTarget, CollectionDropOffTile

# Todo: These methods should be added to the WorldBuilder


def add_collection_goal(builder, collection_locs, collection_objects, name, in_order=False,
                        collection_area_colour="#c87800", collection_area_opacity=1.0, overwrite_goals=False):
    """ Adds a goal to the world to collect objects and drop them in a specific area.

    This is a helper method to quickly add a `CollectionGoal` to the world. A `CollectionGoal` will check if a set of
    objects with certain property-value combinations are at specified locations (potentially in a fixed order). To do
    so, location(s) need to be specified that function as such a "drop off zone". This method add to those locations a
    `CollectionDropOffTile` object, which are searched by the `CollectionGoal` and checks if there the specified objects
    are at those tiles.

    In addition, this method receives a list of dictionaries that represent the kind of objects that need to be
    collected. Since objects are described as a set of properties and their values, these dictionaries contain such
    property-value pairs (with the property names as keys, and their values as values).

    Finally, this method adds a `CollectionGoal` that links these collection tiles and the requested objects. This goal
    checks at each tick if the requested objects are at the specified location(s). If multiple locations are given, the
    requested objects can be spread out over all of those locations! For example, if a Red Block and Blue Block need to
    be collected on locations (0, 0) and  (1, 0), the goal will be accomplished if both blocks are at either location
    but also when the Red Block is at (0, 0) and the Blue Block is at (1, 0) or vice versa.

    Parameters
    ----------
    collection_locs : (x, y) or list/tuple of (x, y)
        A single location where the objects need to be collected, or a list/tuple of such locations. A location is a
        list/tuple of two integers, the x- and y-coordinates respectively.
    collection_objects : list/tuple of dicts, or a RandomProperty with such list/tuple
        A list or tuple of dictionaries. Each dictionary represents a the properties and their respective values that
        identify the to be collected object. It can also be a RandomProperty with as values such a list/tuple. This can
        be used to generate a different collection_objects per world creation.
    name : str
        The name of the `CollectionGoal` and the added `CollectionTarget` and `CollectionDropOffTile` objects.
    in_order : bool (default is False)
        Whether the objects need to be collected and dropped of in the order specified by the `collection_objects` list.
        If all objects are present but not dropped in the right order, the goal will not be accomplished if this is set
        to True.
    collection_area_colour : str (default is )
        The colour of the area on the specified locations representing the drop zone.
    collection_area_opacity : float (default is 1.0)
        The opacity of the area on the specified locations representing the drop zone.
    overwrite_goals : bool (default is False)
        Whether any previously added goals to the builder should be discarded/overwritten.

    Examples
    --------
    Add a collection gaol that requires agents to collect 2 objects in order. The first with the color "#ff0000" (red)
    and the second with the color "#0000ff" (blue). Objects can be dropped at either location (0, 0) or (1, 0). The drop
    off are is called "Dropzone".
    >>> order = [{"visualize_colour": "#ff0000"}, {"visualize_colour": "#0000ff"}]
    >>> builder.add_collection_goal("Dropzone", [(0, 0), (1, 0)], order, in_order=True)

    Add two collection goals, each with the same collection zone. The first goal needs to collect two objects with the
    colours "#ff0000" (red) and "##0000ff" (blue). The second goal needs to collect two objects with the custom property
    "is_candy" set to True. Both goals can be satisfied by dropping a red and blue candy, or by dropping a red and blue
    object that are not candies, and two candies with different colours than red or blue.
    >>> colored_objects = [{"visualize_colour": "#ff0000"}, {"visualize_colour": "#0000ff"}]
    >>> builder.add_collection_goal("Colours", [(0, 0), (1, 0)], colored_objects)
    >>> candy_objects = [{"is_candy": True}, {"is_candy": True}]
    >>> builder.add_collection_goal("Candies", [(0, 0), (1, 0)], candy_objects)

    Add a collection goal to collect a red and blue candy but in a different order every time a world is created. The
    two orders defined here are: first red, then blue OR first blue then red.
    >>> different_orders = [[{"visualize_colour": "#ff0000"}, {"visualize_colour": "#0000ff"}], \
    >>>                     [{"visualize_colour": "#0000ff"}, {"visualize_colour": "#ff0000"}]]
    >>> rp_order = RandomProperty(values=different_orders)
    >>> builder.add_collection_goal("Colours", [(0, 0), (1, 0)], rp_order, in_order=True)


    Notes
    -----
    It is important remember that objects might not be traversable, which prevents them from stacking. So if a goal is
    made that request 2 objects to be collected on the same location where both objects are not traversable, the goal
    will never be able to succeed.

    See Also
    --------
    matrx.goals.CollectionGoal
        The `CollectionGoal` that performs the logic of check that all object(s) are dropped at the drop off tiles.
    matrx.objects.CollectionDropTile
        The tile that represents the location(s) where the object(s) need to be dropped.
    matrx.objects.CollectionTarget
        The invisible object representing which object(s) need to be collected and (if needed) in which order.
    """

    # Check if the `collection_locs` parameter is a list of locations. If it is a single location, make a list out of
    # it. If it are no locations, then raise an exception.
    incorrect_locs = True
    if isinstance(collection_locs, (list, tuple)) and len(collection_locs) > 0:  # locs is indeed a list or tuple
        if len(collection_locs) == 2 and isinstance(collection_locs[0], int) and isinstance(collection_locs[1], int):
            incorrect_locs = False
        else:
            for l in collection_locs:
                if isinstance(l, (list, tuple)) and len(l) == 2 and isinstance(l[0], int) and isinstance(l[1], int):
                    incorrect_locs = False
    if incorrect_locs:
        raise ValueError("The `collection_locs` parameter must be a  list or tuple of length two (e.g. [x, y]) or a "
                         "list of length > 0 containing such lists/tuples (e.g. [[x1, y1], (x2, y2), [x3, y3]]. These "
                         "represent the locations of the area in which the objects need to be collected.")

    # Check if the `collection_objects` is a list/tuple of dictionaries and if it is a RandomProperty, that is values
    # are.
    vals = collection_objects
    if isinstance(vals, RandomProperty):
        vals = vals.values
    if not (isinstance(vals, (list, tuple)) and len(vals) > 0 and isinstance(vals[0], dict)):
        raise ValueError("The `collection_objects` must be a list or tuple of length > 0 containing dictionaries that "
                         "represent an object description of the to be collected objects in terms of property-value "
                         "pairs.")

    # If it is a tuple, cast to list
    if isinstance(collection_objects, tuple):
        collection_objects = list(collection_objects)
    if isinstance(collection_objects, RandomProperty) and isinstance(collection_objects.values, tuple):
        collection_objects.values = list(collection_objects.values)

    # Add the `CollectionDropOffTile` at each of the given locations. These tiles will be used by the `CollectionGoal`
    # to check if all the objects are indeed collected (potentially in the required order as denoted by the order of the
    # `collect_objects` parameter).
    for l in collection_locs:
        builder.add_object(location=l, name=name, callable_class=CollectionDropOffTile,
                           is_traversable=True, is_movable=False, visualize_shape=0,
                           visualize_colour=collection_area_colour, visualize_depth=0,
                           visualize_opacity=collection_area_opacity)

    # Add the `CollectionTarget` object with the specified objects to collect. By default, we add it to the first given
    # collection locations.
    target_name = f"{name}_target"
    builder.add_object(location=collection_locs[0], name=target_name,
                       callable_class=CollectionTarget, collection_objects=collection_objects,
                       collection_zone_name=target_name)

    # Create and add the collection goal
    collection_goal = CollectionGoal(name=name, target_name=target_name, in_order=in_order)
    builder.add_goal(collection_goal, overwrite=overwrite_goals)


# TODO : Was an actual edit in the WorldBuilder, should be added to MATRX repo!
def add_goal(builder, world_goal, overwrite=False):
    """ Appends a `WorldGoal` to the worlds this builder creates.

    Parameters
    ----------
    world_goal : WorldGoal or list/tuple of WorldGoal
        A single world goal or a list/tuple of world goals.
    overwrite : bool (default is False)
        Whether to overwrite the already existing goal in the builder.

    Examples
    --------
    Add a single world goal to a builder, overwriting any previously added goals (e.g. through the builder constructor).
    >>> builder.add_goal(LimitedTimeGoal(100), overwrite=True)

    """
    # Check if the simulation_goal is a SimulationGoal, an int or a list or tuple of SimulationGoal
    if not isinstance(world_goal, (int, WorldGoal, list, tuple)) and len(world_goal) > 0:
        raise ValueError(f"The given simulation_goal {world_goal} should be of type {WorldGoal.__name__} "
                         f"or a list/tuple of {WorldGoal.__name__}, or it should be an int denoting the max"
                         f"number of ticks the world should run (negative for infinite).")

    # Add the world goals
    curr_goals = builder.world_settings["simulation_goal"]
    if not isinstance(curr_goals, (list, tuple)):
        curr_goals = (curr_goals)
    if not isinstance(world_goal, (list, tuple)):
        world_goal = (world_goal)
    goals = curr_goals + world_goal
    builder.world_settings["simulation_goal"] = goals
