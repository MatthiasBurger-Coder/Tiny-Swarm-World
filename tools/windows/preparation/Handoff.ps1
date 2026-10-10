# Pure command rendering; execution remains in the selected interactive Linux console.
function Get-PreparationHandoff($Options,$Facts) {
    $checkout=$Facts.handoff_checkout
    if($Facts.handoff_ready -ne $true -or $checkout -isnot [string] -or $checkout -cnotmatch '\A/[A-Za-z0-9_./ -]+\z' -or $checkout -match '^/mnt/[a-z](?:/|$)' -or $Facts.user -cnotmatch '\A[a-z_][a-z0-9_-]{0,31}\z'){
        return @{status='BLOCKED';preparation_ready=$false;services_verified=$false
            remedy='Place the complete trusted checkout in the selected ordinary Linux account home (default ~/Tiny-Swarm-World), or pass -LinuxCheckout /absolute/Linux/path; rerun -Preflight. No copy or install was executed.'}
    }
    # Restricted path grammar excludes shell metacharacters; single quotes preserve spaces.
    $prefix="cd -- '$checkout' && "
    $prepare=$prefix+'./prepare_linux.sh --service-profile '+$Options.ServiceProfile
    $install=$prefix+'exec ./install.sh --service-profile '+$Options.ServiceProfile
    $chain=$prefix+'./prepare_linux.sh --service-profile '+$Options.ServiceProfile+' && exec ./install.sh --service-profile '+$Options.ServiceProfile
    # PowerShell single-quoted strings escape embedded POSIX quotes by doubling them.
    $command="wsl.exe --distribution '"+$Options.Distro+"' --user '"+$Facts.user+"' --exec /bin/bash -lc '"+$chain.Replace("'","''")+"'"
    return @{status='LINUX_PREPARATION_REQUIRED';distro=$Options.Distro;account=$Facts.user;checkout=$checkout
        prepare_command=$prepare;install_command=$install;operator_command=$command
        preparation_ready=$false;services_verified=$false}
}
