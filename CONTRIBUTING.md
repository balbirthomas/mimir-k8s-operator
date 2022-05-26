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

- Implement charm scale up/down and clustering of Mimir Components
- Handle charm upgrade event
- Handle remote write consumer relation departed event
- Refine charm life cycle with respect to
  + Restart Grafana Mimir workload when necessary (eg. after config changed)
  + Remove alert rules on remote write consumer relation departed events
- Support an Ingress relation
- Implement unit tests
- Implement integration tests
- Provide CI/CD github workflows using Tox

## Testing

### Manual Testing

- Build and deploy this charm
```sh
$ juju deploy ./mimir-k8s_ubuntu-20.04-amd64.charm --resource mimir-image=grafana/mimir:latest
```
- Deploy Grafana agent and Grafana
```sh
$ juju deploy grafana-k8s --channel=edge
$ juju deploy grafana-agent-k8s --channel=edge
```
- Check Mimir is not acquiring any metrics as yet
```sh
$ curl -s http://<MIMI-UNIT-IP-ADDRESS>:9009/api/v1/user_stats
```
- Add a relation between Grafana Agent and Mimir
- Wait a minute or so and now check that Mimir is getting metrics from Grafana agent
- Add a relation between Mimir and Grafana
```sh
$ juju add-relation mimir-k8s grafana-k8s
```
- Login to Grafana dashboard and check there is a Mimir data source
```sh
$ juju run-action grafana-k8s/0 get-admin-password --wait
```
- Check Grafana is getting metrics from Mimir
- Set an alertmanger configuration
```sh
$ curl -X POST --data-binary '@/path/to/alertmanager/config.yaml' -H 'Content-Type: text/x-yaml' http://<MIMIR-UNIT-IP-ADDRESS>:9009/api/v1/alerts
```
- Check alertmanager has been configured set by pointing your browser to
`http://<MIMIR-UNIT-IP-ADDRESS:9009/alertmanager/` i.e. the Mimir Alertmanager UI.
Note the trailing slash. Alternatively the alertmanager configuration may also be
queried using a `curl` commandline
```sh
$ curl -s http://<MIMIR-UNIT-IP-ADDRESS>:9009/api/v1/alerts
```
- Set an alert rule. (Note default tenant ID with multi-tenancy disabled is `anonymous`)
```sh
$ curl --data-binary '@/path/to/alert/rule/cpu_overuse.yaml' -H 'Content-Type: application/yaml' http://<MIMIR-UNIT-IP-ADDRESS>:9009/prometheus/config/v1/rules/anonymous
```
For structure of alert rule file see this [discussion thread](https://github.com/grafana/mimir/discussions/1863))
- Check alert rule has been set using the command line
```sh
$ curl http://<MIMIR-UNIT-IP-ADDRESS>:9009/prometheus/config/v1/rules
```
- Wait for alert rule to fire and check it is firing in the Mimir Alertmanager UI which can be accessed at
`http://<MIMIR-UNIT-IP-ADDRESS>:9009/alertmanager` or alternatively use the following curl commandline to
query alerts
```sh
$ curl -s http://<MIMIR-UNIT-IP-ADDRESS>:9009/prometheus/api/v1/alerts | jq
```
- Delete the alert rule using
```sh
$ curl -X DELETE http://<MIMIR-UNIT-IP-ADDRESS>:9009/prometheus/config/v1/rules/anonymous/<RULE-GROUP-NAME>
```

### Unit Tests
The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:
```sh
    ./run_tests
```
