""" This module implements a dummy data generator. """
import numpy as np


def create_big_daniel(detector_number=1000):
    """
    function generate big daniel data

    :param detector_number: number of entries that will be generated - default number is 1000
    :return data: dict as {'T756_MA_756': [655, 97, 564], 'T772_MA_772': [436, 744, 614],
     'T254_MA_254': [608, 74, 8]...}
    """
    daniel = {}
    for i in range(detector_number):
        arr = np.random.randint(1000, size=3)
        daniel['T' + str(i) + '_MA_' + str(i)] = arr.tolist()

    return daniel


def create_big_detectors(detector_number=10, parent_id=None,
                         detector_root_name="Detector",
                         start_index_for_detector_root_name=0):
    """
    function create big data i.e. detector_name, detector_parent_id relating to
    the detector name, and parent as API add_detector(self, name, parent_id) required

    :param detector_number: number of detectors that well be generated - default number is 10
    :param parent_id: parent path of detector - default None
    :param detector_root_name: base name for a detector - default value is "Detector"
    :param start_index_for_detector_root_name:
           start index of increase progressively with detector root name - default is 0
    :return list with tuples that can be input for pytests.
    :return example [('Detector0', None), ('Detector1', None)...]
    """
    group_detectors = []
    root = detector_root_name
    area = range(start_index_for_detector_root_name,
                 start_index_for_detector_root_name + detector_number)

    for start in area:
        detector_name_root_with_number = root + str(start)
        item = (detector_name_root_with_number, parent_id)
        group_detectors.append(item)

    return group_detectors


def create_multilevel_detectors(level=5,
                                number_subdetectors_of_each_detector=4,
                                detector_root_name="detector",
                                parent_path=None,
                                group_detector_parent=[]):
    """
    function create multilevel of detectors , which is like n-tree
    (each detector has many layers of subdetectors)

    :param level: define layers of detectors tree, default is 5
    :param number_subdetectors_of_each_detector: define number of
           subdetectors for each parent detector, default is 4
    :param detector_root_name: define the base name of detector,
           default value is "detector"
    :param parent_path: specify parent_path of subdetector,
           if there is no basic detector can be used,
           it should be None as create first level detectors, default is None
    :param[inout] group_detector_parent: a list stores
           the data structure of multilevel detector, default is []
    return null. The result will be stored in the group_detector_parent param.

    usage example: create_multilevel_detectors(5, 4, "detector", None, group_detector_parent)
    example explanation: it create a five levels detectors tree each detector has 4 subdetector,
    """

    # level is also used to as a count to achieve recursion;
    # assume [detect, None] is counted as a layer as well
    if level == 0:
        return

    first_level_detector = create_big_detectors(
        number_subdetectors_of_each_detector, parent_path, detector_root_name)

    for first_level_item in first_level_detector:
        group_detector_parent.append(first_level_item)
        detector_name = first_level_item[0]

        if parent_path is None:
            path = detector_name
        else:
            path = parent_path + "/" + detector_name

        create_multilevel_detectors(level - 1, number_subdetectors_of_each_detector,
                                    "sub" + detector_root_name, path,
                                    group_detector_parent)
