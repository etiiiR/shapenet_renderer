$blenderPath = "C:\Program Files\Blender2.7\blender.exe"
$scriptPath = "C:\Users\super\Documents\GitHub\shapenet_renderer\shapenet_spherical_renderer.py"
$meshDir = "C:\Users\super\Documents\GitHub\shapenet_renderer\data\nils"
$outputDir = "C:\Users\super\Documents\GitHub\shapenet_renderer\data\nils\bilder"

Get-ChildItem -Path $meshDir -Recurse -Filter *.stl | ForEach-Object -Parallel {
    & "$using:blenderPath" --background --python "$using:scriptPath" --addons "io_mesh_stl" -- `
        --mesh_fpath $_.FullName `
        --output_dir "$using:outputDir" `
        --num_observations 128
} -ThrottleLimit 4
