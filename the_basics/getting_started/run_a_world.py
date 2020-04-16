from matrx.cases import vis_test

if __name__ == "__main__":
    builder = vis_test.create_builder()
    builder.startup()

    world = builder.get_world()

    world.run(api_info=builder.api_info)