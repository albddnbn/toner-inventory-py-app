$Loop1 = 0
$password_checker = 0
$mysql_install_buffer = 0
$CopyProgramLoop = 0

Add-Type -AssemblyName PresentationFramework

winget -v | Out-Null

if ($?) {
    Write-Host "Winget Found! Proceeding with install"
}
else {
    Write-Host "Winget not found! Please download/update App Installer from Microsoft Store! Link: https://apps.microsoft.com/store/detail/app-installer/9NBLGGH4NNS1?hl=en-us&gl=us&rtc=1"
    exit
}

Write-Host "Downloading dependencies..." 

winget install Microsoft.VCRedist.2015+.x64 --silent --scope machine --accept-source-agreements
winget install --id Python.Python.3.9 --silent --scope machine --accept-source-agreements

$MysqlInstall = Read-Host -Prompt "Do you have Mysql server already installed? (Y/n)" 

while ( $Loop1 -eq 0 ) {

    if ( "$MysqlInstall" -eq "n" ) {
        Invoke-WebRequest -Uri "https://dev.mysql.com/get/Downloads/MySQLInstaller/mysql-installer-web-community-8.0.32.0.msi" -OutFile "C:\Users\Public\mysql-installer-web-community-8.0.32.0.msi"
        [System.Windows.MessageBox]::Show("MySQL-Server IS REQUIRED! Default options are good, set your own root password. Installer will launch after you close this window.", "Window title", "OK", [System.Windows.MessageBoxImage]::Information)
        Start-Process -FilePath "msiexec.exe" -ArgumentList "/i C:\Users\Public\mysql-installer-web-community-8.0.32.0.msi" -Wait
        while ( $mysql_install_buffer -eq 0 ) {
            $MysqlInstallFinished = Read-Host -Prompt "Is MySQL done installing? (Y/n)"
            if ( $MysqlInstallFinished -eq "Y" ) {
                Write-Host "Resuming Script..."
                $mysql_install_buffer = 1
            }
            else {
                Write-Host "Please wait for MySQL to finish installing!"
            }

        }
        $Loop1 = 1
    }

    elseif ( "$MysqlInstall" -eq "Y" ) {
        Write-Host "Continuing with install..."
        $Loop1 = 1
    }

    else {
        Write-Host "Invalid resposne. Try again!"
    }

}

# (Get-Content -Path "pythonpackages.bat" | Select-Object -First 3) | Set-Content -Path "pythonpackages.bat"

while ( $password_checker -eq 0 ) {

    $MysqlPasswordSecure = Read-Host -Prompt "What is your mysql root password?" -AsSecureString
    $root_password = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($MysqlPasswordSecure))

    & 'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe' -u root -p"$root_password" -e "exit" 2>$null

    if ($Error[0].Exception.Message -like '*Access denied for user*') {
        Write-Host "Incorrect MySql Password. Try again!"
    }
    else {
        Write-Host "Password Correct!"
        $password_checker = 1
        $MysqlPasswordSecure = 0
    }

}

(Get-Content "$PSScriptRoot\..\config\config.yaml") -replace '(password:).*', '$1' | Set-Content "$PSScriptRoot\..\config\config.yaml"
(Get-Content "$PSScriptRoot\..\config\config.yaml") | ForEach-Object { $_.Replace('password:', "password: $root_password") } | Set-Content "$PSScriptRoot\..\config\config.yaml"

(Get-Content "$PSScriptRoot\initializedb.bat") -replace '(root_password=).*', '$1' | Set-Content "$PSScriptRoot\initializedb.bat"
(Get-Content "$PSScriptRoot\initializedb.bat") | ForEach-Object { $_.Replace('root_password=', "root_password=$root_password") } | Set-Content "$PSScriptRoot\initializedb.bat"


Start-Process -FilePath "$PSScriptRoot\initializedb.bat" -Wait

# Add-Content -Path $PSScriptRoot\pythonpackages.bat -Value ("`n" + (Get-Content $PSScriptRoot\..\requirements.txt | ForEach-Object { "%pip% $_" } | Out-String))

# Start-Process -FilePath "$PSScriptRoot\pythonpackages.bat" -Wait

$root_password = 0

while ( $CopyProgramLoop -eq 0 ) {


    do {
        $CopyProgram = Read-Host -Prompt "Would you like to copy to another directory? (Y/n)"
    } while ($CopyProgram -ne "Y" -and $CopyProgram -ne "n")




    if ( $CopyProgram -eq "Y" ) {
        $Destination = Read-Host -Prompt "What directory would you like to move it to?"

        do {
            $response = Read-Host "Confirm correct directory: $Destination [Y/n]"
        } while ($response -ne "Y" -and $response -ne "n")

        if ($response -eq "Y") {
            Copy-Item -Path "$PSScriptRoot\..\" -Destination "$Destination\" -Recurse
        }

    }
    else {
        $CopyProgramLoop = 1	
    }



}


do {
    $LaunchProgram = Read-Host -Prompt "Want to launch?(Y/n)"
} while ($LaunchProgram -ne "Y" -and $LaunchProgram -ne "n")

if ( $LaunchProgram -eq "Y") {
    Set-Location $PSScriptRoot\..\
    #Start-Process -FilePath ".\main.python3.9.bat"
    Start-Process -FilePath ".\Printer Inventory App v1.0.1.exe"
}


