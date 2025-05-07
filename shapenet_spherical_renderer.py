import argparse
import numpy as np
import os
import sys
sys.path.append(os.path.dirname(__file__))
import bpy
from mathutils import Vector
import util
import blender_interface

# CLI args
p = argparse.ArgumentParser(description='Render meshes into PixelNeRF-style train/val/test splits.')
p.add_argument('--mesh_dir', type=str, required=True, help='Directory of .obj or .stl meshes.')
p.add_argument('--output_dir', type=str, required=True, help='Base output directory.')
p.add_argument('--num_observations', type=int, default=50, help='Number of views per object for training.')
p.add_argument('--resolution', type=int, default=128, help='Image resolution.')
argv = sys.argv[sys.argv.index("--") + 1:]
opt = p.parse_args(argv)

# Output subdirs
train_dir = os.path.join(opt.output_dir, "pollen_train")
val_dir   = os.path.join(opt.output_dir, "pollen_val")
test_dir  = os.path.join(opt.output_dir, "pollen_test")
os.makedirs(train_dir, exist_ok=True)
os.makedirs(val_dir, exist_ok=True)
os.makedirs(test_dir, exist_ok=True)

# Mesh list (sorted = stable index-based split)
mesh_files = sorted([
    os.path.join(opt.mesh_dir, f)
    for f in os.listdir(opt.mesh_dir)
    if f.lower().endswith(('.obj', '.stl'))
])

# Index-based split (PixelNeRF-style)
n = len(mesh_files)
n_train = int(0.8 * n)
n_val = int(0.1 * n)
splits = {
    "train": mesh_files[:n_train],
    "val":   mesh_files[n_train:n_train + n_val],
    "test":  mesh_files[n_train + n_val:]
}

# Renderer
renderer = blender_interface.BlenderInterface(resolution=opt.resolution)

# Per-split rendering
for split_name, files in splits.items():
    print("Rendering {} meshes for split: {}".format(len(files), split_name))
    split_output = {
        "train": train_dir,
        "val": val_dir,
        "test": test_dir
    }[split_name]

    for mesh_idx, mesh_fpath in enumerate(files):
        mesh_name = os.path.splitext(os.path.basename(mesh_fpath))[0]
        instance_dir = os.path.join(split_output, mesh_name)

        # Compute bounding radius
        renderer.import_mesh(mesh_fpath, scale=1., object_world_matrix=None)
        obj = bpy.context.selected_objects[0]
        bbox_corners = [obj.matrix_world * Vector(corner) for corner in obj.bound_box]
        center = sum(bbox_corners, Vector((0.0, 0.0, 0.0))) / 8.0
        radius = max((v - center).length for v in bbox_corners)
        sphere_radius = radius * 2.0
        bpy.ops.object.select_all(action='DESELECT')
        obj.select = True
        bpy.ops.object.delete()

        # Use different view counts based on split
        if split_name == 'train':
            cam_locations = util.sample_spherical(opt.num_observations, sphere_radius)
        else:
            cam_locations = util.get_archimedean_spiral(sphere_radius, 250)

        obj_location = np.zeros((1, 3))
        cv_poses = util.look_at(cam_locations, obj_location)
        blender_poses = [util.cv_cam2world_to_bcam2world(m) for m in cv_poses]

        # Identity object pose
        rot_mat = np.eye(3)
        hom_coords = np.array([[0., 0., 0., 1.]])
        obj_pose = np.concatenate((rot_mat, obj_location.reshape(3, 1)), axis=-1)
        obj_pose = np.concatenate((obj_pose, hom_coords), axis=0)

        # Final import + render
        renderer.import_mesh(mesh_fpath, scale=1., object_world_matrix=obj_pose)
        renderer.render(instance_dir, blender_poses, write_cam_params=True)
