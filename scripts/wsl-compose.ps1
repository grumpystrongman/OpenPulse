param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$ComposeArgs
)

if (-not $ComposeArgs -or $ComposeArgs.Count -eq 0) {
  $ComposeArgs = @('ps')
}

$joined = [string]::Join(' ', ($ComposeArgs | ForEach-Object { $_.Replace("'", "''") }))
wsl -d Ubuntu -e sh -lc "cd /mnt/c/Users/grump/OpenPulse && docker compose $joined"
