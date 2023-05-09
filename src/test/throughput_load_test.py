import random
import string

from locust import HttpUser, task, between


# precondition: start server on 6000 port and create voting with the name "Voting 1"
class VotingUser(HttpUser):
    wait_time = between(1, 5)
    host = "http://127.0.0.1:6000"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.candidate_index = 0

    @task
    def add_candidate(self):
        self.candidate_index += 1
        body = {
            "contract": "Voting 1",
            "candidate": ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)) + str(
                self.candidate_index)
        }
        self.client.put("/contract/candidate", json=body)
