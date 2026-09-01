import time
from network_monitor import collect_metrics


def main():
    print("=" * 50)
    print("Detectra AI - Real-Time Network Agent")
    print("=" * 50)
    print("Agent started successfully.")
    print("Collecting real network data...")
    print()

    while True:
        metrics = collect_metrics()

        print("Real Network Metrics:")
        print(f"Latency       : {metrics['latency']} ms")
        print(f"Packet Loss   : {metrics['packet_loss']} %")
        print(f"Jitter        : {metrics['jitter']} ms")
        print(f"Network Usage : {metrics['network_usage']} %")
        print(f"CPU Usage     : {metrics['cpu_usage']} %")
        print(f"Connections   : {metrics['active_connections']}")
        print(f"Network Errors: {metrics['network_errors']}")
        print(f"Connected     : {metrics['connectivity_ok']}")
        print("-" * 50)

        time.sleep(5)


if __name__ == "__main__":
    main()