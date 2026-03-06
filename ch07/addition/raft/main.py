import time
import random
import logging

from raft_server import RaftServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d  %(message)s",
    datefmt="%H:%M:%S",
)

CLUSTER_SIZE = 5


def find_leader(servers):
    for s in servers:
        st = s.get_state()
        if st["role"] == "LEADER":
            return s
    return None


def print_cluster(servers):
    print(f"  {'ID':>2}  {'ROLE':9}  {'TERM':>5}  {'LOG':>5}  {'COMMIT':>6}  {'KV STORE'}")
    print("  " + "-" * 58)
    for s in servers:
        st     = s.get_state()
        marker = "  <-- leader" if st["role"] == "LEADER" else ""
        print(
            f"  S{st['id']}  {st['role']:9}  {st['term']:5d}  "
            f"{st['log_len']:5d}  {st['commit']:6d}  {st['kv']}{marker}"
        )
    print()


def simulate_cluster():
    # Build a cluster: each server knows its peers after all are created.
    servers = [RaftServer(i, CLUSTER_SIZE) for i in range(CLUSTER_SIZE)]
    for s in servers:
        s.peers = [p for p in servers if p.id != s.id]
    for s in servers:
        s.start()

    print(f"Raft cluster of {CLUSTER_SIZE} servers started.")
    print("Press Ctrl-C to stop.\n")
    print("Waiting for initial leader election ...\n")
    time.sleep(1.0)   # let the first election settle

    counter = 0
    try:
        while True:
            time.sleep(1.5)

            leader = find_leader(servers)
            if leader:
                counter += random.randint(1, 10)
                ok, lid = leader.client_request(("SET", "counter", counter))
                if ok:
                    print(f"[CLIENT]  SET counter={counter}  -- accepted by S{lid}")
                else:
                    redirect = f"S{lid}" if lid is not None else "unknown"
                    print(f"[CLIENT]  S{leader.id} is no longer leader, hint: {redirect}")
            else:
                print("[CLIENT]  no leader available, waiting ..")

            print_cluster(servers)

    except KeyboardInterrupt:
        print("\nShutting down cluster ..")
        for s in servers:
            s.stop()


if __name__ == "__main__":
    simulate_cluster()
