
# check if $profile exists, if not create it
if (!(Test-Path -Path $PROFILE ))
{ New-Item -Type File -Path $PROFILE -Force }

# current folder
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition

# check if # lords-asm-for-mc-begin comment exists in $profile, if so remove everything between # lords-asm-for-mc-begin and # lords-asm-for-mc-end
if (Select-String -Path $PROFILE -Pattern "lords-asm-for-mc-begin") {
    Write-Host "Removing previous installation of 'lords-asm-for-mc' from $PROFILE"
    $content = Get-Content $PROFILE -Raw
    $content = $content -replace "(?ms)(\# lords-asm-for-mc-begin)(.*?)(\# lords-asm-for-mc-end)\s*", ""
    Set-Content $PROFILE $content
}

# install requirements
Write-Host "Installing dependencies for 'lords-asm-for-mc' in $root using pip"
pip install -r requirements.txt

# add # lords-asm-for-mc-begin comment to $profile
"# lords-asm-for-mc-begin" | Out-File -FilePath $PROFILE -Append
"# do not edit, remove or change these comments, it is used by 'lords-asm-for-mc' to install and uninstall itself" | Out-File -FilePath $PROFILE -Append

# add alias to compile.py
$compile = Join-Path $root "compile.py"
"function lor { $input | python `"$compile`" @args }" | Out-File -FilePath $PROFILE -Append

# add alias to send.py
$send = Join-Path $root "tools" "send.py"
"function rfsend { $input | python `"$send`" @args }" | Out-File -FilePath $PROFILE -Append

Write-Host "Alias 'lor' and 'rfsend' created in $PROFILE"

# add $root to the PATH, if not already there
"`$env:PATH  += `";$root`"" | Out-File -FilePath $PROFILE -Append
Write-Host "Added '$root' to the PATH"

"# lords-asm-for-mc-end" | Out-File -FilePath $PROFILE -Append

Write-Host "Done"
Write-Host "You may need to restart your PowerShell session for changes to take effect"