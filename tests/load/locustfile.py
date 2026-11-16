
import random
import uuid
from locust import HttpUser, task, between


class PharmaSafeUser(HttpUser):
    wait_time = between(1, 3)

    @task(4)
    def submit_case(self):
        case_id = f"LOAD-{uuid.uuid4().hex[:12]}"

        payload = {
            "case_id": case_id,
            "drug_name": random.choice([
                "DemoDrug-A",
                "DemoDrug-B",
                "DemoDrug-C"
            ]),
            "reaction_description": random.choice([
                "Synthetic report of a mild skin reaction.",
                "Synthetic report of a headache after medication.",
                "Synthetic report of mild nausea."
            ]),
            "patient_age": random.randint(18, 85),
            "patient_sex": random.choice(["male", "female", "other"]),
            "onset_date": "2026-11-15T10:00:00Z",
            "drug_start_date": "2026-11-10T10:00:00Z",
            "outcome": "recovering",
            "reporter_type": "patient"
        }

        with self.client.post(
            "/api/v1/cases",
            json=payload,
            name="/api/v1/cases",
            catch_response=True
        ) as response:

            if response.status_code == 202:
                response.success()
            else:
                response.failure(
                    f"Unexpected status: {response.status_code}"
                )

    @task(1)
    def health_check(self):
        self.client.get("/health", name="/health")
