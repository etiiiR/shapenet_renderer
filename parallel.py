import os
import subprocess
from multiprocessing import Pool

# === CONFIGURATION ===
blender_path = r"C:\Program Files\Blender2.7\blender.exe"
script_path = r"C:\Users\super\Documents\GitHub\shapenet_renderer\shapenet_spherical_renderer_multi_core.py"
mesh_dir = r"C:\Users\super\Documents\Github\sequoia\data\processed\interim"
output_dir = r"C:\Users\super\Documents\GitHub\shapenet_renderer\128_views"
num_observations = "128"
resolution = "256"
split_name = "train"
#split_name = "val"
#split_name = "test"
num_processes =12

def render_single_mesh(mesh_path, max_retries=3):
    mesh_name = os.path.splitext(os.path.basename(mesh_path))[0]
    attempt = 0
    while attempt < max_retries:
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
            #"--orthogonal",
        ]

        print(f"[INFO] Launching Blender for: {mesh_name} (attempt {attempt+1})")
        print(" ".join(cmd))

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            print(f"[DONE] Finished: {mesh_name}")
            print("Blender output:\n", result.stdout)
            return  # Success, exit the function
        else:
            print(f"[ERROR] Rendering failed for {mesh_name} (attempt {attempt+1})")
            print("STDERR:\n", result.stderr)
            print("STDOUT:\n", result.stdout)
            attempt += 1

    print(f"[FAIL] All attempts failed for {mesh_name}")

if __name__ == "__main__":
    mesh_files = [
        os.path.join(mesh_dir, f)
        for f in os.listdir(mesh_dir)
        if f.lower().endswith(('.stl', '.obj'))
    ]

    print(f"[INFO] Found {len(mesh_files)} mesh files. Starting rendering with {num_processes} workers...")
    
    with Pool(processes=num_processes) as pool:
        pool.map(render_single_mesh, mesh_files)

    print("[INFO] All rendering tasks completed.")
