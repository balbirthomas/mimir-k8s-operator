# Mimir Operator

## Overview

This documents explains the processes and practices recommended for
contributing enhancements to the Prometheus charm.

- Generally, before developing enhancements to this charm, you should consider
  [opening an issue ](https://github.com/balbirthomas/mimir-k8s-operator) explaining
  your use case.
- If you would like to chat with us about your use-cases or proposed
  implementation, you can reach us at
  [Canonical Mattermost public channel](https://chat.charmhub.io/charmhub/channels/charm-dev)
  or [Discourse](https://discourse.charmhub.io/).
  The primary author of this charm is available on the Mattermost channel as
  `@balbir-thomas`.
- Familiarising yourself with the
  [Charmed Operator Framework](https://juju.is/docs/sdk)
  library will help you a lot when working on new features or bug fixes.
- All enhancements require review before being merged. Code review
  typically examines
  + code quality
  + test coverage
  + user experience for Juju administrators
  this charm.
- Please help us out in ensuring easy to review branches by rebasing
  your pull request branch onto the `main` branch. This also avoids
  merge commits and creates a linear Git commit history.

## Developing

Create and activate a virtualenv with the development requirements:

```sh
$ virtualenv -p python3 venv
$ source venv/bin/activate
```

### Build and deploy charm

This section provides a few tips on how to interact with the Mimir workload using
its API to aid debugging during development.

- Build and deploy this charm
```sh
$ charmcraft pack
$ juju deploy ./mimir-k8s_ubuntu-20.04-amd64.charm --resource mimir-image=grafana/mimir:latest
```

### Add charm relations

- Deploy Grafana agent and Grafana
```sh
$ juju deploy grafana-k8s --channel=edge
$ juju deploy grafana-agent-k8s --channel=edge
```

### Inspect charm behaviour

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

## Testing

### Linting

Code linting is supported using

```sh
$ tox -e lint
```

To fix any linting errors use

```sh
$ tox -e fmt
```

### Unit Tests
Unit tests may be run using the command line

```sh
$ tox -e unit
```

### Integration Tests

Integration tests may be run using the command line

```sh
$ tox -e integration
```

## Roadmap

- Support relation with an object storage provider charm.
- Support relation with cache provider charms through which object storage may be proxied.
- Implement ingester shutdown with flush to object storage workflow.
- Implement HA Tracker support both in Mimir Charm and Prometheus Remote Write Library.
- Implement a Mimir tester charm that can support wide range of integration tests.
- Implement end to end test cases with multiple Grafana Agents scraping the same
  metrics endpoint and remote writing to multiple Mimir instances.
- Benchmark charm under load to evaluate scalability.
