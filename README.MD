To start the node:
python api.py --api_port=6000 --p2p_port=5000

Existing issues:

1. ```BrokenPipeError: [Errno 32] Broken pipe ``` sometimes happens during block creation (Most probably because of the
   way PoET is implemented) - Fixed
