(Get-Content -Path "pythonpackages.bat" | Select-Object -First 3) | Set-Content -Path "pythonpackages.bat"
Add-Content -Path $PSScriptRoot\pythonpackages.bat -Value ("`n" + (Get-Content $PSScriptRoot\..\requirements.txt | ForEach-Object { "%pip% $_" } | Out-String))
Start-Process -FilePath "$PSScriptRoot\pythonpackages.bat" -Wait