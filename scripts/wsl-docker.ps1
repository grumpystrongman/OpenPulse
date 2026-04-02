param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$DockerArgs
)

if (-not $DockerArgs -or $DockerArgs.Count -eq 0) {
  $DockerArgs = @('version')
}

wsl -d Ubuntu -- docker @DockerArgs
