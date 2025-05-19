$blenderPath = "C:\Program Files\Blender2.7\blender.exe"
$scriptPath = "C:\Users\super\Documents\GitHub\shapenet_renderer\shapenet_spherical_renderer_multi_core.py"
$meshDir = "C:\Users\super\Documents\GitHub\seqouia\data\processed\interim"
$outputDir = "C:\Users\super\Documents\GitHub\shapenet_renderer\data\256\"

# STEP 1: Generate split_summary.json
& python $scriptPath --mesh_dir $meshDir --output_dir $outputDir

# STEP 2: Load split_summary.json
$splitSummary = Get-Content "$outputDir\split_summary.json" | ConvertFrom-Json

$jobs = @()
foreach ($splitName in @("train", "val", "test")) {
    foreach ($meshName in $splitSummary.$splitName) {
        $meshPath = Join-Path $meshDir "$meshName.stl"

        $cmd = "`"$blenderPath`" --background --python `"$scriptPath`" -- " +
               "--mesh_fpath `"$meshPath`" --output_dir `"$outputDir`" " +
               "--split_name $splitName --object_name $meshName"

        # Start as parallel job
        $jobs += Start-Job -ScriptBlock { param($c) Invoke-Expression $c } -ArgumentList $cmd
        Start-Sleep -Milliseconds 300  # Stagger launches a bit
    }
}

# STEP 3: Wait for all jobs to finish
$jobs | Wait-Job
