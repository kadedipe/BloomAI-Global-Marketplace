import importlib.util
from pathlib import Path

module_path = Path(__file__).parents[1] / "worker.py"
spec = importlib.util.spec_from_file_location("worker", module_path)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)

def test_process_valid_event():
    worker.process('{"name":"product.created","schema_version":1,"payload":{"product_id":1}}')
