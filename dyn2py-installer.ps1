$InnoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

# Check if innosetup installed
if (-not (Test-Path -Path $InnoSetupPath -PathType Leaf)) {
    throw "Innosetup not found!"    
} 

# Copy dyn2py.exe from default folder:
if (Test-Path -Path ".\dist\dyn2py.exe" -PathType Leaf) {
    Copy-Item ".\dist\dyn2py.exe" -Destination "." -Force
} 

# Check if dyn2py.exe exists at all
if (-not(Test-Path -Path ".\dist\dyn2py.exe" -PathType Leaf)) {
    throw "dyn2py.exe not found!"    
}

# Read version number from pyproject.toml and update in innosetup:
$regex = Select-String -Path pyproject.toml -Pattern '^version = "((?:\d\.){2}\d)"$'
$version = $regex.Matches.Groups[1].Value
(Get-Content dyn2py-installer.iss).Replace("x.x.x", $version) | Set-Content dyn2py-installer.iss

# Build:
& $InnoSetupPath -Qp $(Join-Path $PWD.Path dyn2py-installer.iss)
