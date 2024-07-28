# Check if $PROFILE exists, if not create it
if (!(Test-Path -Path $PROFILE)) {
    New-Item -Type File -Path $PROFILE -Force
}

# Current folder
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Check if # lords-asm-for-mc-begin comment exists in $PROFILE, if so remove everything between # lords-asm-for-mc-begin and # lords-asm-for-mc-end
if (Select-String -Path $PROFILE -Pattern "# lords-asm-for-mc-begin") {
    Write-Host "Removing previous installation of 'lords-asm-for-mc' from $PROFILE"
    $content = Get-Content $PROFILE -Raw
    $content = $content -replace "(?ms)(\# lords-asm-for-mc-begin)(.*?)(\# lords-asm-for-mc-end)\s*", ""
    Set-Content $PROFILE $content
}

# Create a virtual environment
$venv_dir = Join-Path $root "venv"
if (-Not (Test-Path -Path $venv_dir)) {
    Write-Host "Creating virtual environment in $venv_dir"
    python -m venv $venv_dir
}

# Define the path to the Python executable within the virtual environment
$venv_python = Join-Path $venv_dir "Scripts\python.exe"

# Install requirements using the virtual environment's Python
& $venv_python -m pip install -r "$root\requirements.txt"

# Add # lords-asm-for-mc-begin comment to $PROFILE
"# lords-asm-for-mc-begin" | Out-File -FilePath $PROFILE -Append -Encoding ASCII
"# do not edit, remove or change these comments, it is used by 'lords-asm-for-mc' to install and uninstall itself" | Out-File -FilePath $PROFILE -Append -Encoding ASCII

# Add alias to compile.py
$compile = Join-Path $root "compile.py"
"function lor { `$input | & `"$venv_python`" `"$compile`" @args }" | Out-File -FilePath $PROFILE -Append -Encoding ASCII

# Add alias to send.py
$send = Join-Path $root "tools/send.py"
"function rfsend { `$input | & `"$venv_python`" `"$send`" @args }" | Out-File -FilePath $PROFILE -Append -Encoding ASCII

Write-Host "Alias 'lor' and 'rfsend' created in $PROFILE"

# Add $root to the PATH, if not already there
if ($env:PATH -notcontains $root) {
    "`$env:PATH += `";$root`"" | Out-File -FilePath $PROFILE -Append -Encoding ASCII
}

Write-Host "Added '$root' to the PATH"

"# lords-asm-for-mc-end" | Out-File -FilePath $PROFILE -Append -Encoding ASCII

Write-Host "Done"
Write-Host "You may need to restart your PowerShell session for changes to take effect"
