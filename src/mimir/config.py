MIMIR_PORT = 9009
MIMIR_PUSH_PATH = "/api/v1/push"
MIMIR_CONFIG_FILE = "/etc/mimir/config.yaml"

MIMIR_DIRS = {
    "bucket_store": "/tmp/mimir/tsdb-sync",
    "data": "/tmp/mimir/data/tsdb",
    "tsdb": "/tmp/mimir/tsdb",
    "compactor": "/tmp/mimir/compactor",
    "rules": "/tmp/mimir/rules",
    "data-alertmanager": "/tmp/mimir/data-alertmanager",
    "tenant-rules": "/tmp/mimir/rules/anonymous",
}


def block_storage_config(s3_config):
    cfg = {
        "bucket_store": {"sync_dir": MIMIR_DIRS["bucket_store"]},
        "tsdb": {"dir": MIMIR_DIRS["tsdb"]},
    }

    if s3_config:
        cfg["backend"] = "s3"
        cfg["s3"] = s3_config
    else:
        cfg["backend"] = "filesystem"
        cfg["filesystem"] = {"dir": MIMIR_DIRS["data"]}

    return cfg


def compactor_config():
    cfg = {
        "data_dir": MIMIR_DIRS["compactor"],
        "sharding_ring": {"kvstore": {"store": "memberlist"}},
    }

    return cfg


def distributor_config():
    cfg = {"ring": {"instance_addr": "127.0.0.1", "kvstore": {"store": "memberlist"}}}

    return cfg


def ingester_config(npeers):
    cfg = {
        "ring": {
            "instance_addr": "127.0.0.1",
            "kvstore": {
                "store": "memberlist",
            },
            "replication_factor": npeers,
        }
    }

    return cfg


def ruler_config():
    cfg = {"alertmanager_url": f"http://localhost:{MIMIR_PORT}/alertmanager"}

    return cfg


def ruler_storage_config():
    cfg = {"backend": "filesystem", "filesystem": {"dir": MIMIR_DIRS["rules"]}}

    return cfg


def server_config():
    cfg = {"http_listen_port": MIMIR_PORT, "log_level": "error"}

    return cfg


def store_gateway_config(npeers):
    cfg = {"sharding_ring": {"replication_factor": npeers}}

    return cfg


def alertmanager_storage_config():
    cfg = {
        "backend": "filesystem",
        "filesystem": {"dir": MIMIR_DIRS["data-alertmanager"]},
    }

    return cfg


def memberlist_config(nodename, peers):
    cfg = {"node_name": nodename, "join_members": list(peers.values())}

    return cfg
