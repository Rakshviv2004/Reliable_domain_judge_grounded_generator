from dotenv import load_dotenv

from monitoring.tracking import init_run

load_dotenv()
run = init_run("smoke-test", {"purpose": "phase0"})
run.log({"hello": 1})
run.finish()
