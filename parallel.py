import os
import subprocess
from multiprocessing import Pool

# === CONFIGURATION ===
blender_path = r"C:\Program Files\Blender2.7\blender.exe"
script_path = r"C:\Users\super\Documents\GitHub\shapenet_renderer\shapenet_spherical_renderer_multi_core.py"
mesh_dir = r"C:\Users\super\Documents\Github\sequoia\data\processed\interim"
output_dir = r"C:\Users\super\Documents\GitHub\shapenet_renderer\parallel_output"
num_observations = "128"
resolution = "256"
split_name = "train"
num_processes = 32  # Number of parallel Blender instances

def render_single_mesh(mesh_path):
    mesh_name = os.path.splitext(os.path.basename(mesh_path))[0]
    
    cmd = [
        blender_path,
        "--background",
        "--python", script_path,
        "--addons", "io_mesh_stl",  # Required for STL import
        "--",
        "--mesh_fpath", mesh_path,
        "--output_dir", output_dir,
        "--split_name", split_name,
        "--object_name", mesh_name,
        "--num_observations", num_observations,
        "--resolution", resolution
    ]

    print(f"[INFO] Launching Blender for: {mesh_name}")
    print(" ".join(cmd))  # Print full command for debugging

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Output Blender logs for inspection
    if result.returncode != 0:
        print(f"[ERROR] Rendering failed for {mesh_name}")
        print("STDERR:\n", result.stderr)
        print("STDOUT:\n", result.stdout)
    else:
        print(f"[DONE] Finished: {mesh_name}")
        print("Blender output:\n", result.stdout)

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
