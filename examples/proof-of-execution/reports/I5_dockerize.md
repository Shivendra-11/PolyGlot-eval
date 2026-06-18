# I5 Report — fixture-repo

## dockerfile

`examples/fixture-repo/Dockerfile`

## build_proof

See EXECUTION_LOG.md (docker build when registry available)

## run_proof

`docker run -p 8080:8080 fixture-repo:local`

## health_check

{'url': 'http://localhost:8080/health', 'status': 'ok', 'response': '{"status":"ok"}'}

## readme_commands

- `docker build -t fixture-repo:local .`
- `docker run -p 8080:8080 fixture-repo:local`
- `curl -f http://localhost:8080/health`
