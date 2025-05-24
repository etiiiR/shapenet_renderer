import os
import subprocess
from multiprocessing import Pool
import json
from functools import partial

# === CONFIGURATION ===
blender_path    = r"C:\Program Files\Blender2.7\blender.exe"
script_path     = r"C:\Users\super\Documents\GitHub\shapenet_renderer\shapenet_spherical_renderer_multi_core.py"

# now points at your augmentation root with subfolders
augmentation_root = r"C:\Users\super\Documents\GitHub\shapenet_renderer\augmentation"
output_dir        = r"C:\Users\super\Documents\GitHub\shapenet_renderer\128_views\256_res"
split_file        = os.path.join(output_dir, "splits.json")

num_observations = "128"
resolution       = "256"
num_processes    = 12

# same camera styles
split_camera_style = {
    "train": "spherical",
    "val":   "spiral",
    "test":  "orthogonal"
}


def load_splits(path):
    with open(path, "r") as f:
        return json.load(f)


def collect_augmented_meshes(splits):
    """
    Walks each aug subfolder and returns a dict:
      { "train": [full_paths...],
        "val":   [...],
        "test":  [...] }
    """
    split_sets = {s: set(splits[s]) for s in splits}
    collected = {s: [] for s in splits}

    for aug_type in os.listdir(augmentation_root):
        aug_dir = os.path.join(augmentation_root, aug_type)
        if not os.path.isdir(aug_dir):
            continue

        for fn in os.listdir(aug_dir):
            if not fn.lower().endswith(".stl"):
                continue

            # split off the marker "_{aug_type}_"
            marker = f"_{aug_type}_"
            if marker not in fn:
                continue
            base = fn.split(marker)[0] + ".stl"

            # find which split this original belongs to
            for split in split_sets:
                if base in split_sets[split]:
                    collected[split].append(os.path.join(aug_dir, fn))
                    break
            else:
                # not in any split — skip
                pass

    return collected


def render_single_mesh(mesh_path, split_name, cam_style, max_retries=3):
    mesh_name = os.path.splitext(os.path.basename(mesh_path))[0]
    for attempt in range(1, max_retries+1):
        cmd = [
            blender_path,
            "--background",
            "--python", script_path,
            "--addons", "io_mesh_stl",
            "--",
            "--mesh_fpath", mesh_path,
            "--output_dir", output_dir,
            "--split_name", split_name,
            "--object_name", mesh_name,
            "--num_observations", num_observations,
            "--resolution", resolution,
        ]
        if cam_style == "orthogonal":
            cmd.append("--orthogonal")

        print(f"[INFO] [{split_name}][{cam_style}] {mesh_name} (attempt {attempt})")
        result = subprocess.run(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
        if result.returncode == 0:
            print(f"[DONE] {mesh_name}")
            return
        else:
            print(f"[ERROR] {mesh_name} failed (attempt {attempt})")
            print(result.stderr)

    print(f"[FAIL] {mesh_name} after {max_retries} attempts")


if __name__ == "__main__":
    # load your 70/15/15 split
    splits = load_splits(split_file)

    # build list of *all* augmented meshes per split
    mesh_groups = collect_augmented_meshes(splits)
    for split in ["train", "val", "test"]:
        meshes = mesh_groups[split]
        cam_style = split_camera_style[split]
        print(f"\n=== SPLIT={split} has {len(meshes)} augmented meshes → cam={cam_style}")

        # dispatch in parallel
        worker = partial(render_single_mesh,
                         split_name=split,
                         cam_style=cam_style)
        with Pool(processes=num_processes) as pool:
            pool.map(worker, meshes)

        print(f"[INFO] done rendering split {split}")
