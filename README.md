# mimir-k8s-operator

## Description

[Mimir][Mimir] is a horizontally scalable, highly available, multi-tenant, long-term storage for Prometheus. This repository contains a [Juju][Juju] charm for Mimir. This charm deploys Mimir in [Monolithic Mode][Monolithic Mode], with Mimir [Alertmanager][Alertmanager] enabled.

## Usage

Deploy the Mimir, Grafana and Grafana Agent
```sh
$ juju deploy mimir-k8s
$ juju deploy grafana-agent-k8s
$ juju deploy grafana-k8s
```
Add a relation with Grafana agent and Grafana
```sh
$ juju add-relation mimir-k8s grafana-agent-k8s
$ juju add-relation mimir-k8s grafana
```
Self monitoring metrics from Grafana agent shold now be visibile in the Grafana dashboard. On relating Grafana Agent charm to any other client charm, the metrics from the client charms will also become visible in the Grafana dashboard.

## Relations

This current supports the relations with the following charms
- [Grafana Agent][Grafana Agent Charm] for ingestion of metrics using Prometheus Remote Write.
- [Grafana][Grafana Charm] for visualization of metrics using Grafana Dashboards.

## OCI Images

This charm uses the latest version of the Grafana Mimir docker image.

## Contributing

Please see the [Juju SDK docs][Juju SDK] for guidelines
on enhancements to this charm following best practice guidelines, and
[`CONTRIBUTING.md`](CONTRIBUTING.md) for developer guidance.

[Mimir]: https://grafana.com/oss/mimir/
[Juju]: https://juju.is
[Juju SDK]: https://juju.is/docs/sdk
[Monolithic Mode]: https://grafana.com/docs/mimir/latest/operators-guide/architecture/deployment-modes/#monolithic-mode
[Alertmanager]: https://grafana.com/docs/mimir/latest/operators-guide/architecture/components/alertmanager/
[Grafana Agent Charm]: https://charmhub.io/grafana-agent-k8s
[Grafana Charm]: https://charmhub.io/grafana-k8s
