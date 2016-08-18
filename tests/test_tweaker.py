from MeshTweaker import Tweak
from FileHandler import FileHandler
import os


def test_area_acumulation():
    test_file = os.path.join(os.path.dirname(__file__), 'test_object.stl')
    mesh = FileHandler.loadMesh(test_file)

    tweaker = Tweak(mesh=mesh, parallel_mode=False, verbose=False)

    # setup tweaker
    content = tweaker.arrange_mesh(mesh)
    default_norm = [0, 0, -1]

    # test area cumulation
    top_n_areas = tweaker.area_cumulation(content=content, n=default_norm)

    print(top_n_areas)

    # check output of tweaker
    expected_areas = [[[1.0, 0.0, 0.0], 3398.5106],
                      [[-1.0, 0.0, 0.0], 3596.7468],
                      [[0.0, -0.642787, -0.766045], 63.5133],
                      [[0.0, -0.642788, -0.766044], 160.4646],
                      [[-0.0, 0.642787, 0.766045], 460.4009],
                      [[0.0, 0.766044, -0.642788], 56.2261]]
    assert len(top_n_areas) == len(expected_areas)
    for expected_area in expected_areas:
        # TODO: improve comparison of floats
        assert expected_area in top_n_areas
