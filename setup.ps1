
# check if $profile exists, if not create it
if (!(Test-Path -Path $PROFILE ))
{ New-Item -Type File -Path $PROFILE -Force }

# current folder
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition

# check if # lords-asm-for-mc-begin comment exists in $profile, if so remove everything between # lords-asm-for-mc-begin and # lords-asm-for-mc-end
if (Select-String -Path $PROFILE -Pattern "lords-asm-for-mc-begin") {
    Write-Host "Removing previous installation of 'lords-asm-for-mc' from $PROFILE."
    $content = Get-Content $PROFILE -Raw
    $content = $content -replace "(?ms)(\# lords-asm-for-mc-begin)(.*?)(\# lords-asm-for-mc-end)\s*", ""
    Set-Content $PROFILE $content
}

Write-Host "Installing dependencies for 'lords-asm-for-mc' in $root using pip."
# install requirements
pip install -r requirements.txt

# add # lords-asm-for-mc-begin comment to $profile.CurrentUserAllHosts (with a newline)
"# lords-asm-for-mc-begin" | Out-File -FilePath $PROFILE -Append

# Define the alias Name: lor, Value: python $compile, Description: Lord's ASM Compiler, add to $profile
$compile = Join-Path $root "compile.py"

# funcytion lor that calls python $compile with arguments, write to $profile
"function lor { python `"$compile`" $args }" | Out-File -FilePath $PROFILE -Append

# Inform the user
Write-Host "Alias 'lor' created for 'python $compile' and added to $PROFILE."

# add $root to the PATH, if not already there
if ($env:Path -notlike "*$root*") {
    $env:Path += ";$root"
    Write-Host "Added '$root' to the PATH."
}

"# lords-asm-for-mc-end" | Out-File -FilePath $PROFILE -Append

Write-Host "You may need to restart your PowerShell session for changes to take effect."