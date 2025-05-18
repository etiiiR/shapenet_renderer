import argparse
import os
import sys
import random
import bpy
from mathutils import Vector

# === CLI Args ===
parser = argparse.ArgumentParser(description="Deform .stl pollen meshes into new augmented variants.")
parser.add_argument("--mesh_dir", type=str, required=True, help="Folder with input STL files")
parser.add_argument("--output_dir", type=str, required=True, help="Folder to save augmented meshes")
parser.add_argument("--num_augmentations", type=int, default=3, help="Number of augmentations per type")
argv = sys.argv[sys.argv.index("--") + 1:]
opt = parser.parse_args(argv)
print("Input folder:", opt.mesh_dir)
# === Helper: Clear Scene ===
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

# === Helper: Normalize to Unit Sphere ===
def normalize_object(obj):
    bpy.context.scene.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
    bpy.ops.object.transform_apply(scale=True)
    bbox = [obj.matrix_world * Vector(corner) for corner in obj.bound_box]
    center = sum(bbox, Vector((0.0, 0.0, 0.0))) / 8.0
    radius = max((v - center).length for v in bbox)
    scale = 1.0 / radius
    obj.scale = (scale, scale, scale)
    bpy.context.scene.update()

# === Deformation Functions ===
def apply_twist(obj, angle_deg):
    # Create an empty as origin for deform
    empty = bpy.data.objects.new("EmptyTwist", None)
    bpy.context.scene.objects.link(empty)
    empty.location = obj.location

    mod = obj.modifiers.new("Twist", type='SIMPLE_DEFORM')
    mod.deform_method = 'TWIST'
    mod.origin = empty
    mod.angle = angle_deg * 3.14159 / 180.0  # degrees to radians


def apply_subsurf(obj, levels=2):
    m = obj.modifiers.new("Subsurf", type='SUBSURF')
    m.levels = levels

def apply_displace(obj, strength, noise_scale, negative=False):
    tex = bpy.data.textures.new("DisplaceTex", type='CLOUDS')
    tex.noise_scale = noise_scale
    tex.intensity = 1.0
    mod = obj.modifiers.new("Displace", type='DISPLACE')
    mod.texture = tex
    mod.strength = -strength if negative else strength

def apply_laplacian_smooth(obj, repeat=10):
    mod = obj.modifiers.new("LaplacianSmooth", type='LAPLACIANSMOOTH')
    mod.iterations = repeat
    mod.lambda_factor = 0.5


def apply_stretch(obj, factor):
    empty = bpy.data.objects.new("EmptyStretch", None)
    bpy.context.scene.objects.link(empty)
    empty.location = obj.location

    mod = obj.modifiers.new("Stretch", type='SIMPLE_DEFORM')
    mod.deform_method = 'TAPER'
    mod.origin = empty
    mod.factor = factor

# === Main Processing ===
deformations = {
    "swelling": lambda obj: (apply_displace(obj, 0.2, 0.3), apply_subsurf(obj)),
    "shriveling": lambda obj: apply_displace(obj, 0.15, 0.5, negative=True),
    "softening": lambda obj: apply_laplacian_smooth(obj),
    "twisting": lambda obj: apply_twist(obj, random.uniform(10, 45)),
    "stretching": lambda obj: apply_stretch(obj, random.uniform(0.2, 0.6)),
}

# Create folders
for deform_type in deformations.keys():
    deform_path = os.path.join(opt.output_dir, deform_type)
    if not os.path.exists(deform_path):
        os.makedirs(deform_path)

for fname in os.listdir(opt.mesh_dir):
    if not fname.lower().endswith(".stl"):
        continue

    base_name = os.path.splitext(fname)[0]
    input_path = os.path.join(opt.mesh_dir, fname)

    for deform_name, deform_func in deformations.items():
        deform_output_dir = os.path.join(opt.output_dir, deform_name)

        for i in range(opt.num_augmentations):
            clear_scene()

            # Import and normalize
            bpy.ops.import_mesh.stl(filepath=input_path)
            obj = bpy.context.selected_objects[0]
            normalize_object(obj)

            # Apply deformation
            deform_func(obj)

            # Apply all modifiers
            bpy.ops.object.convert(target='MESH')

            # Export
            out_name = "{}_{}_{}.stl".format(base_name, deform_name, i + 1)
            out_path = os.path.join(deform_output_dir, out_name)
            bpy.ops.export_mesh.stl(filepath=out_path, use_selection=True)
            print("✅ Saved:", out_path)

print("🎉 All augmentations complete.")