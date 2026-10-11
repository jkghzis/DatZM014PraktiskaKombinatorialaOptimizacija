$ErrorActionPreference = "SilentlyContinue"

$computer = Get-CimInstance Win32_ComputerSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$os = Get-CimInstance Win32_OperatingSystem
$bios = Get-CimInstance Win32_BIOS
$board = Get-CimInstance Win32_BaseBoard
$gpu = Get-CimInstance Win32_VideoController
$ramModules = Get-CimInstance Win32_PhysicalMemory
$disks = Get-CimInstance Win32_DiskDrive
$logicalDisks = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3"
$net = Get-CimInstance Win32_NetworkAdapterConfiguration |
    Where-Object { $_.IPEnabled } |
    Select-Object -First 1

# RAM totals
$ramBytes = [double]$computer.TotalPhysicalMemory
$ramGB = [math]::Round($ramBytes / 1GB, 2)

# CPU information
$cpuMaxGHz = [math]::Round($cpu.MaxClockSpeed / 1000, 2)

# Memory module summary
$ramModuleDetails = $ramModules | ForEach-Object {
    [PSCustomObject]@{
        CapacityGB = [math]::Round($_.Capacity / 1GB, 2)
        SpeedMHz   = $_.Speed
        ConfiguredSpeedMHz = $_.ConfiguredClockSpeed
        Manufacturer = $_.Manufacturer
        PartNumber = $_.PartNumber.Trim()
    }
}

# GPU summary
$gpuDetails = $gpu | ForEach-Object {
    [PSCustomObject]@{
        Name = $_.Name
        DriverVersion = $_.DriverVersion
        VRAM_GB = if ($_.AdapterRAM) {
            [math]::Round($_.AdapterRAM / 1GB, 2)
        } else {
            "Unknown"
        }
        Resolution = "$($_.CurrentHorizontalResolution)x$($_.CurrentVerticalResolution)"
    }
}

# Physical disk summary
$diskDetails = $disks | ForEach-Object {
    [PSCustomObject]@{
        Model = $_.Model.Trim()
        SizeGB = [math]::Round($_.Size / 1GB, 2)
        Interface = $_.InterfaceType
        MediaType = $_.MediaType
    }
}

# Logical disk summary
$volumeDetails = $logicalDisks | ForEach-Object {
    [PSCustomObject]@{
        Drive = $_.DeviceID
        FileSystem = $_.FileSystem
        SizeGB = [math]::Round($_.Size / 1GB, 2)
        FreeGB = [math]::Round($_.FreeSpace / 1GB, 2)
    }
}

# Main report
$report = [PSCustomObject]@{
    ComputerName = $computer.Name
    Manufacturer = $computer.Manufacturer
    Model = $computer.Model
    SystemType = $computer.SystemType

    CPU = $cpu.Name.Trim()
    CPU_SocketCount = $computer.NumberOfProcessors
    CPU_PhysicalCores = $cpu.NumberOfCores
    CPU_LogicalProcessors = $cpu.NumberOfLogicalProcessors
    CPU_MaxClockGHz = $cpuMaxGHz

    RAM_TotalGB = $ramGB
    RAM_ModuleCount = @($ramModules).Count
    RAM_Modules = ($ramModuleDetails | ForEach-Object {
        "$($_.CapacityGB) GB @ $($_.ConfiguredSpeedMHz) MHz"
    }) -join "; "

    GPU = ($gpu.Name -join "; ")
    OperatingSystem = $os.Caption
    OS_Version = $os.Version
    OS_Build = $os.BuildNumber
    OS_Architecture = $os.OSArchitecture

    BIOS_Version = $bios.SMBIOSBIOSVersion
    Motherboard = "$($board.Manufacturer) $($board.Product)"

    PowerShellVersion = $PSVersionTable.PSVersion.ToString()
    LogicalProcessorsAvailableToOS = $env:NUMBER_OF_PROCESSORS
}

Write-Host "`n=== PC SPECIFICATIONS ===" -ForegroundColor Cyan
$report | Format-List

Write-Host "`n=== GPU DETAILS ===" -ForegroundColor Cyan
$gpuDetails | Format-Table -AutoSize

Write-Host "`n=== RAM MODULES ===" -ForegroundColor Cyan
$ramModuleDetails | Format-Table -AutoSize

Write-Host "`n=== PHYSICAL DISKS ===" -ForegroundColor Cyan
$diskDetails | Format-Table -AutoSize

Write-Host "`n=== STORAGE VOLUMES ===" -ForegroundColor Cyan
$volumeDetails | Format-Table -AutoSize

# Export main report to CSV
$outputPath = Join-Path $PWD "pc-specifications.csv"
$report | Export-Csv -Path $outputPath -NoTypeInformation -Encoding UTF8

Write-Host "`nMain report saved to: $outputPath" -ForegroundColor Green
