
from flask import Flask, request
from uuid import uuid4
from celery import Celery, shared_task
from celery.result import AsyncResult
from time import sleep
import tasks

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        CELERY=dict(
            broker_url="redis://localhost",
            result_backend="redis://localhost",
            task_ignore_result=True,
        ),
    )
    app.config.from_prefixed_env()
    celery_app = tasks.celery_init_app(app)

    in_memory_versions = {
        "V1": {"address": "pricing-api.domain"},
        "V2": {"address": "pricing-api-2.domain"}
    }


    in_memory_pricing = {
        "property": 15,
        "engineering": 10,
        "marine": 5
    }

    @shared_task(ignore_result=False)
    def pricing_task(pricing, body, uid, address) -> str:
        #mock curl command ala
        #curl address/uid body
        print(body)
        print(address)
        sl = in_memory_pricing[pricing]
        sleep(sl)
        return 'slept ' + str(sl) + ' seconds for uid ' + str(uid)
        

    @app.post('/<version>/<pricing>/request')
    def request_pricing(version, pricing):
        calculationId = uuid4()
        pr = pricing_task.delay(pricing = pricing, body = request.get_json(force=True), uid = calculationId, address = in_memory_versions[version]["address"])
        return {"result_id": pr.id, "calculation_id": calculationId}

    @app.get("/result/<id>")
    def task_result(id: str):
        result = AsyncResult(id)
        return {
            "ready": result.ready(),
            "successful": result.successful(),
            "value": result.result if result.ready() else None,
        }

    return app