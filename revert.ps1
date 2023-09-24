# remove alias from $profile
if (Select-String -Path $PROFILE -Pattern "lords-asm-for-mc-begin") {
    Write-Host "Removing installation of 'lords-asm-for-mc' from $PROFILE."
    $content = Get-Content $PROFILE -Raw
    $content = $content -replace "(?ms)(\# lords-asm-for-mc-begin)(.*?)(\# lords-asm-for-mc-end)\s*", ""
    Set-Content $PROFILE $content
}