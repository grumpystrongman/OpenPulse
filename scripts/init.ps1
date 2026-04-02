param(
  [switch]$NoBuild
)

if (!(Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
}

if ($NoBuild) {
  docker compose up -d
} else {
  docker compose up -d --build
}

docker compose ps
