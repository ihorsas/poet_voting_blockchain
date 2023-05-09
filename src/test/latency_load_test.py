from locust import HttpUser, task


# precondition: start server on 6000 port
class VotingUser(HttpUser):
    host = "http://127.0.0.1:6000"

    @task
    def my_task(self):
        self.client.get("/blockchain")
