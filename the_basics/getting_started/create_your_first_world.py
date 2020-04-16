from matrx import WorldBuilder


def create_builder():
    size = [25, 25]
    builder = WorldBuilder(shape=size, run_matrx_api=True,
                           run_matrx_visualizer=True)
    
    return builder


if __name__ == "__main__":
    builder = create_builder()
    builder.startup()

    world = builder.get_world()

    world.run(api_info=builder.api_info)
