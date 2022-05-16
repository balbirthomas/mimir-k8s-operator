# mimir

## Developing

Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Code overview

This charm supports three relations
- Grafana Agent
- Grafana
- Ingress

## Intended use case

This charm manages Grafana Mimir in monolithic mode.

## Roadmap

If this Charm doesn't fulfill all of the initial functionality you were
hoping for or planning on, please add a Roadmap or TODO here

## Testing

### Manual Testing

- Build and deploy this charm
```
juju deploy ./mimir-k8s_ubuntu-20.04-amd64.charm --resource mimir-image=grafana/mimir:latest
```
- Deploy Grafana agent and Grafana
```
juju deploy grafana-k8s --channel=edge
juju deploy grafana-agent-k8s --channel=edge
```
- Check Mimir is not acquiring any metrics as yet
```
curl -s http://<MIMI-UNIT-IP-ADDRESS>:9009/api/v1/user_stats
```
- Add a relation between Grafana Agent and Mimir
- Wait a minute or so and now check that Mimir is geting metrics from Grafana agent
- Add a relation between Mimir and Grafana
```
juju add-relation mimir-k8s grafana-k8s
```
- Login to Grafana dashboard and check there is a Mimir data source
```
juju run-action grafana-k8s/0 get-admin-password --wait
```
- Check Grafana is getting metrics from Mimir

### Unit Tests
The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:

    ./run_tests
