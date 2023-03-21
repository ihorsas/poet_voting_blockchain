import argparse

from src.api.api_server import ApiServer

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Start Blockchain node")
    parser.add_argument("--api_port", type=int, help="Port to interact with blockchain via API")
    parser.add_argument("--p2p_port", type=int, help="Port for your node to communicate with other nodes in the network")
    args = parser.parse_args()

    ApiServer(args.api_port, args.p2p_port)