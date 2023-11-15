import os

import numpy as np
from opensfm import io
from opensfm import pydense
from opensfm.dataset import DataSet, UndistortedDataSet
import json

def run_dataset(data: DataSet, image_list, corrections_file: str) -> None:
    """ Export reconstruction to OpenMVS format. """

    udata = data.undistorted_dataset()
    reconstructions = udata.load_undistorted_reconstruction()
    tracks_manager = udata.load_undistorted_tracks_manager()

    offset = [0, 0, 0]
    obb_min = [0, 0, 0]
    obb_max = [0, 0, 0]
    if corrections_file:
        with open(corrections_file, "r") as f:
            correction_data = json.load(f)
            if "offset" in correction_data:
                offset = [
                    correction_data["offset"]["x"],
                    correction_data["offset"]["y"],
                    correction_data["offset"]["z"],
                ]
            if "obb" in correction_data:
                if "min" in correction_data["obb"]:
                    obb_min = [
                        correction_data["obb"]["min"]["x"],
                        correction_data["obb"]["min"]["y"],
                        correction_data["obb"]["min"]["z"],
                    ]
                if "max" in correction_data["obb"]:
                    obb_max = [
                        correction_data["obb"]["max"]["x"],
                        correction_data["obb"]["max"]["y"],
                        correction_data["obb"]["max"]["z"],
                    ]
                
    export_only = None
    if image_list:
        export_only = {}
        with open(image_list, "r") as f:
            for image in f:
                export_only[image.strip()] = True

    if reconstructions:
        export(reconstructions[0], tracks_manager, udata, export_only, offset, obb_min, obb_max)


def export(reconstruction, tracks_manager, udata: UndistortedDataSet, export_only, offset, obb_min, obb_max) -> None:
    exporter = pydense.OpenMVSExporter()
    exporter.set_obb_min(obb_min[0], obb_min[1], obb_min[2])
    exporter.set_obb_max(obb_max[0], obb_max[1], obb_max[2])
    for camera in reconstruction.cameras.values():
        if camera.projection_type == "perspective":
            w, h = camera.width, camera.height
            K = np.array(
                [
                    [camera.focal * max(w, h), 0, (w - 1.0) / 2.0],
                    [0, camera.focal * max(w, h), (h - 1.0) / 2.0],
                    [0, 0, 1],
                ]
            )
            exporter.add_camera(str(camera.id), K, w, h)

    shots_map = {}
    total_behind = 0

    for shot in reconstruction.shots.values():
        if export_only is not None and shot.id not in export_only:
            continue

        if shot.camera.projection_type == "perspective":
            image_path = udata._undistorted_image_file(shot.id)
            mask_path = udata._undistorted_mask_file(shot.id)
            if not os.path.isfile(mask_path):
                mask_path = ""

            shots_map[str(shot.id)] = shot
            
            origin = shot.pose.get_origin()

            exporter.add_shot(
                str(os.path.abspath(image_path)),
                str(os.path.abspath(mask_path)),
                str(shot.id),
                str(shot.camera.id),
                shot.pose.get_rotation_matrix(),
                [origin[0] - offset[0], origin[1] -offset[1], origin[2] - offset[2]]
            )

    def positive_point_depth(point, shot_id):
        if not shot_id in shots_map:
            return False

        shot = shots_map[shot_id]

        # Is point in front of the camera?
        is_behind = shot.pose.transform(point.coordinates)[2] > 0
        if is_behind:
            nonlocal total_behind
            total_behind+=1
        return is_behind

    for point in reconstruction.points.values():
        observations = tracks_manager.get_track_observations(point.id)

        if export_only is not None:
            shots = [k for k in observations if k in export_only]
        else:
            shots = list(observations)

        if shots:
            shots = [s for s in shots if positive_point_depth(point, s)]

        if shots:
            coordinates = np.array(point.coordinates, dtype=np.float64)
            exporter.add_point([coordinates[0] - offset[0], coordinates[1] - offset[1], coordinates[2] - offset[2]], shots)

    print("Removed %d shots found behind the camera" % total_behind)
    io.mkdir_p(udata.data_path + "/openmvs")
    exporter.export(udata.data_path + "/openmvs/scene.mvs")
