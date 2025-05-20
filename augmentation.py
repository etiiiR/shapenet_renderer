import argparse
import os
import sys
import json
import random
import bpy
from mathutils import Vector

class FastPollenAugmentor:
    """
    Optimized pollen mesh augmentation pipeline with resume capability.
    - On abort/restart, skips already processed meshes.
    - Stores progress in 'progress.json' under output_dir.
    """
    PROGRESS_FILE = 'progress.json'

    def __init__(self, mesh_dir, output_dir, num_augmentations=3, decimate_ratio=0.2, seed=42):
        self.mesh_dir = mesh_dir
        self.output_dir = output_dir
        self.num_augmentations = num_augmentations
        self.decimate_ratio = decimate_ratio
        random.seed(seed)
        # Define deformation methods
        self.deformations = {
            'twisting': self._twisting,
            'stretching': self._stretching,
            'groove': self._groove,
            'asymmetry': self._asymmetry,
            'full_combo': self._full_combo,
            'radical_reshape': self._radical_reshape,
            'lobed': self._lobed,
            'irregular': self._irregular,
            'ellipsoid': self._ellipsoid,
        }
        self._prepare_workspace()
        self.progress = self._load_progress()
        
    def _make_modifier_first(self, obj, mod):
        while obj.modifiers[0] != mod:
            bpy.ops.object.modifier_move_up(modifier=mod.name)

    def _prepare_workspace(self):
        for name in self.deformations:
            out = os.path.join(self.output_dir, name)
            if not os.path.exists(out):
                os.makedirs(out)
        tex1 = bpy.data.textures.new('TexSwelling', type='CLOUDS')
        tex2 = bpy.data.textures.new('TexShrivel', type='CLOUDS')
        self.tex_swelling = tex1
        self.tex_shrivel = tex2

    def _load_progress(self):
        path = os.path.join(self.output_dir, self.PROGRESS_FILE)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return {}

    def _save_progress(self):
        path = os.path.join(self.output_dir, self.PROGRESS_FILE)
        with open(path, 'w') as f:
            json.dump(self.progress, f)

    def clear_scene(self):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

    def import_and_reduce(self, filepath):
        self.clear_scene()
        bpy.ops.import_mesh.stl(filepath=filepath)
        obj = bpy.context.selected_objects[0]
        bbox = [obj.matrix_world * Vector(c) for c in obj.bound_box]
        center = sum(bbox, Vector((0,0,0))) / 8.0
        r = max((v-center).length for v in bbox)
        if r > 0:
            obj.scale = (1.0/r, 1.0/r, 1.0/r)
        mod = obj.modifiers.new('Decimate', type='DECIMATE')
        mod.ratio = self.decimate_ratio
        bpy.ops.object.modifier_apply(modifier=mod.name)
        return obj

    def bake_and_export(self, obj, out_path):
        bpy.ops.object.select_all(action='DESELECT')
        obj.select = True
        bpy.ops.export_mesh.stl(filepath=out_path, use_selection=True)
        bpy.data.objects.remove(obj, do_unlink=True)

    def _twisting(self, obj, t):
            # Randomly rotate the object to twist along a random axis
            original_rotation = obj.rotation_euler[:]
            obj.rotation_euler = (
                random.uniform(0, 2 * 3.14159),
                random.uniform(0, 2 * 3.14159),
                random.uniform(0, 2 * 3.14159)
            )
            mod = obj.modifiers.new('Twist', type='SIMPLE_DEFORM')
            mod.deform_method = 'TWIST'
            # Make the twist angle more pronounced and random
            base_angle = 0.1 + t * 0.4
            mod.angle = base_angle * random.uniform(-1.2, 1.2)
            # Apply the modifier and reset rotation
            bpy.context.scene.objects.active = obj
            bpy.ops.object.select_all(action='DESELECT')
            obj.select = True
            bpy.ops.object.modifier_apply(modifier=mod.name)
            obj.rotation_euler = original_rotation

    def _stretching(self, obj, t):
        # Randomly rotate the object to stretch in a random direction
        original_rotation = obj.rotation_euler[:]
        obj.rotation_euler = (
            random.uniform(0, 3.1415 * 2),
            random.uniform(0, 3.1415 * 2),
            random.uniform(0, 3.1415 * 2)
        )
        mod = obj.modifiers.new('Taper', type='SIMPLE_DEFORM')
        mod.deform_method = 'TAPER'
        base_factor = (0.08 + t * 0.35) / 2.5
        mod.factor = base_factor * random.uniform(0.85, 1.25)
        # Add a subtle displacement for surface detail
        tex = bpy.data.textures.new('StretchDisplace', type='CLOUDS')
        tex.noise_scale = 0.13 + t * 0.07
        mod_disp = obj.modifiers.new('StretchDisplace', type='DISPLACE')
        mod_disp.texture = tex
        mod_disp.strength = 0.015 + t * 0.03
        # Apply the modifier and reset rotation
        bpy.context.scene.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        obj.select = True
        bpy.ops.object.modifier_apply(modifier=mod.name)
        obj.rotation_euler = original_rotation
        

    def _groove(self, obj, t):
        original_rotation = obj.rotation_euler[:]
        obj.rotation_euler = (1.5708, 0.0, 0.0)
        mod = obj.modifiers.new('GrooveTwist', type='SIMPLE_DEFORM')
        mod.deform_method = 'BEND'
        # Make the bend a bit more pronounced
        base_angle = -0.15 - t * 0.3
        mod.angle = base_angle * random.uniform(0.8, 1.2)
        bpy.context.scene.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        obj.select = True
        self._make_modifier_first(obj, mod)
        bpy.ops.object.modifier_apply(modifier=mod.name)
        obj.rotation_euler = original_rotation
    
        # Add a subtle displacement for a wavy groove effect
        tex = bpy.data.textures.new('GrooveDisplace', type='CLOUDS')
        tex.noise_scale = 0.12 + t * 0.08
        mod_disp = obj.modifiers.new('GrooveDisplace', type='DISPLACE')
        mod_disp.texture = tex
        mod_disp.strength = 0.02 + t * 0.04

    def _asymmetry(self, obj, t):
        mod = obj.modifiers.new('TiltDeform', type='SIMPLE_DEFORM')
        mod.deform_method = 'TAPER'
        base_factor = 0.10 + t * 0.30  # doubled from 0.05 + t * 0.15
        mod.factor = base_factor * random.uniform(0.6, 1.6)  # wider range
        obj.rotation_euler = (
            random.uniform(-0.24, 0.24),  # doubled from -0.12, 0.12
            random.uniform(-0.24, 0.24),
            random.uniform(-0.24, 0.24)
        )
        # Add a subtle displacement for surface asymmetry
        tex = bpy.data.textures.new('AsymDisplace', type='CLOUDS')
        tex.noise_scale = 0.36 + t * 0.16  # doubled noise scale
        mod_disp = obj.modifiers.new('AsymDisplace', type='DISPLACE')
        mod_disp.texture = tex
        mod_disp.strength = 0.06 + t * 0.14  # doubled strength
            
    def _ellipsoid(self, obj, t):
        scale_x = 1.0 + t * random.uniform(0.2, 0.5)
        scale_y = 1.0 - t * random.uniform(0.1, 0.3)
        scale_z = 1.0 + t * random.uniform(0.1, 0.3)
        obj.scale = (scale_x, scale_y, scale_z)
        
    def _lobed(self, obj, t):
        mod = obj.modifiers.new('LobedSimple', type='SIMPLE_DEFORM')
        mod.deform_method = 'BEND'
        mod.angle = random.uniform(-0.5, 0.5) * (1 + t)
        # Optionally, add a lattice modifier for more complex lobes
        
    def _irregular(self, obj, t):
        deform_choices = [
            lambda o: o.modifiers.new('RandTwist', type='SIMPLE_DEFORM').deform_method == 'TWIST',
            lambda o: o.modifiers.new('RandBend', type='SIMPLE_DEFORM').deform_method == 'BEND',
            lambda o: o.modifiers.new('RandTaper', type='SIMPLE_DEFORM').deform_method == 'TAPER',
            lambda o: o.modifiers.new('RandStretch', type='SIMPLE_DEFORM').deform_method == 'STRETCH',
            lambda o: o.modifiers.new('RandCast', type='CAST'),
            lambda o: o.modifiers.new('RandDisplace', type='DISPLACE'),
            lambda o: o.modifiers.new('RandLattice', type='LATTICE'),
            lambda o: o.modifiers.new('RandWave', type='WAVE'),
            lambda o: o.modifiers.new('RandSmooth', type='SMOOTH'),
        ]
        for _ in range(random.randint(2, 4)):
            deform = random.choice(deform_choices)
            deform(obj)


    def _radical_reshape(self, obj, t):
        # Apply a strong bend for radical shape, but keep the surface smooth
        mod_bend = obj.modifiers.new('BigBend', type='SIMPLE_DEFORM')
        mod_bend.deform_method = 'BEND'
        mod_bend.angle = random.uniform(-1.2, 1.2) * (0.7 + t)
        # Optionally, add a cast for more radical but smooth reshaping
        if random.random() < 0.5:
            mod_cast = obj.modifiers.new('RadicalCast', type='CAST')
            mod_cast.cast_type = random.choice(['SPHERE', 'CYLINDER'])
            mod_cast.factor = 0.8 + t * random.uniform(0.1, 0.4)
            mod_cast.use_x = mod_cast.use_y = mod_cast.use_z = True
        # Optionally, add a lattice for organic but smooth deformation
        if random.random() < 0.5:
            lat_data = bpy.data.lattices.new('RadicalLat')
            lat_data.points_u = lat_data.points_v = lat_data.points_w = 4
            lat = bpy.data.objects.new('RadicalLatObj', lat_data)
            bpy.context.scene.objects.link(lat)
            lat.location = obj.location
            lat.scale = obj.dimensions
            mod_lat = obj.modifiers.new('RadicalLattice', type='LATTICE')
            mod_lat.object = lat
            bpy.context.scene.objects.active = lat
            bpy.ops.object.mode_set(mode='EDIT')
            base_amp = 0.01 + t * 0.03
            for p in lat.data.points:
                dist = sum(abs(x - 0.5) for x in p.co_deform) / 1.5
                amp = base_amp * (0.7 + 0.5 * dist)
                p.co_deform = (
                    p.co_deform[0] + random.uniform(-amp, amp),
                    p.co_deform[1] + random.uniform(-amp, amp),
                    p.co_deform[2] + random.uniform(-amp, amp)
                )
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.scene.objects.active = obj

    def _full_combo(self, obj, t):
        print("[ℹ️] Running full_combo with multiple moderate deformations")
        base_twist = 0.01 + t * 0.03
        mod_twist = obj.modifiers.new('Twist', type='SIMPLE_DEFORM')
        mod_twist.deform_method = 'TWIST'
        mod_twist.angle = base_twist * random.uniform(0.8, 1.2)
        base_bend = -0.01 - t * 0.03
        mod_bend = obj.modifiers.new('Bend', type='SIMPLE_DEFORM')
        mod_bend.deform_method = 'BEND'
        mod_bend.angle = base_bend * random.uniform(0.8, 1.2)
        base_taper = 0.003 + t * 0.012
        mod_taper = obj.modifiers.new('Taper', type='SIMPLE_DEFORM')
        mod_taper.deform_method = 'TAPER'
        mod_taper.factor = base_taper * random.uniform(0.8, 1.2)
        base_stretch = 0.003 + t * 0.012
        mod_stretch = obj.modifiers.new('Stretch', type='SIMPLE_DEFORM')
        mod_stretch.deform_method = 'STRETCH'
        mod_stretch.factor = base_stretch * random.uniform(0.8, 1.2)
        lat_data = bpy.data.lattices.new('LatCombo')
        lat_data.points_u = lat_data.points_v = lat_data.points_w = 4
        lat = bpy.data.objects.new('LatObjCombo', lat_data)
        bpy.context.scene.objects.link(lat)
        lat.location = obj.location
        lat.scale = obj.dimensions
        mod_lat = obj.modifiers.new('LatticeCombo', type='LATTICE')
        mod_lat.object = lat
        bpy.context.scene.objects.active = lat
        bpy.ops.object.mode_set(mode='EDIT')
        base_amp = 0.0015 + t * 0.004
        amp_factor = random.uniform(0.8, 1.2)
        for p in lat.data.points:
            dist = sum(abs(x - 0.5) for x in p.co_deform) / 1.5
            amp = base_amp * (0.7 + 0.5 * dist) * amp_factor
            p.co_deform = (
                p.co_deform[0] + random.uniform(-amp, amp),
                p.co_deform[1] + random.uniform(-amp, amp),
                p.co_deform[2] + random.uniform(-amp, amp)
            )
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.scene.objects.active = obj
        bpy.ops.object.select_all(action='DESELECT')
        obj.select = True
        bpy.ops.object.convert(target='MESH')

    def augment(self):
        files = [f for f in os.listdir(self.mesh_dir) if f.lower().endswith('.stl')]
        for fname in files:
            mesh_prog = self.progress.get(fname, {})
            base = self.import_and_reduce(os.path.join(self.mesh_dir, fname))
            for name, fn in self.deformations.items():
                completed = mesh_prog.get(name, -1)
                out_dir = os.path.join(self.output_dir, name)
                for i in range(completed + 1, self.num_augmentations):
                    print('Processing {0} {1} ({2}/{3})'.format(fname, name, i + 1, self.num_augmentations))
                    t = float(i) / (self.num_augmentations - 1) * 0.4 if self.num_augmentations > 1 else 0
                    dup = base.copy()
                    dup.data = base.data.copy()
                    bpy.context.scene.objects.link(dup)
                    result = fn(dup, t)
                    if result is None:
                        result = dup
                    out_name = '{0}_{1}_{2}.stl'.format(os.path.splitext(fname)[0], name, i + 1)
                    self.bake_and_export(result, os.path.join(out_dir, out_name))
                    mesh_prog[name] = i
                    self.progress[fname] = mesh_prog
                    self._save_progress()
        print('🎉 All augmentations done.')

if __name__=='__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--mesh_dir', required=True)
    p.add_argument('--output_dir', required=True)
    p.add_argument('--num_augmentations', type=int, default=5)
    p.add_argument('--decimate_ratio', type=float, default=1.0)
    p.add_argument('--seed', type=int, default=42)
    args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    aug = FastPollenAugmentor(args.mesh_dir, args.output_dir, args.num_augmentations, args.decimate_ratio, args.seed)
    aug.augment()