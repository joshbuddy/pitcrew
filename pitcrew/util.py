from pitcrew.executor import ExecutionResult
import base64
import sys
import json


class OutputEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            try:
                return obj.decode("utf-8", "strict")
            except UnicodeDecodeError:
                return base64.b64encode(obj)
        elif isinstance(obj, Exception):
            return str(obj)
        elif isinstance(obj, ExecutionResult):
            return {
                "context": obj.context.descriptor(),
                "result": obj.result,
                "exception": obj.exception,
            }
        else:
            return json.JSONEncoder.default(self, obj)


class ResultsPrinter:
    def __init__(self, results):
        self.results = results

    def print(self):
        results = self.results
        if results.passed:
            sys.stderr.write("Passed:\n")
            sys.stdout.write(json.dumps(results.passed, cls=OutputEncoder))
            sys.stdout.flush()
            sys.stderr.write("\n")
        if results.failed:
            sys.stderr.write("Failed:\n")
            sys.stderr.write(json.dumps(results.failed, cls=OutputEncoder))
            sys.stderr.write("\n")
            sys.stderr.flush()
        if results.errored:
            sys.stderr.write("Errored:\n")
            sys.stderr.write(json.dumps(results.errored, cls=OutputEncoder))
            sys.stderr.write("\n")
            sys.stderr.flush()

        sys.stderr.write(f"\n 🔧🔧🔧 Finished 🔧🔧🔧\n")

        sys.stderr.write("\nSummary")
        if len(results.passed) != 0:
            sys.stderr.write(f" \033[32mpassed={len(results.passed)}\033[0m")
        else:
            sys.stderr.write(f" passed={len(results.passed)}")

        if len(results.failed) != 0:
            sys.stderr.write(f" \033[31mfailed={len(results.failed)}\033[0m")
        else:
            sys.stderr.write(f" failed={len(results.failed)}")

        if len(results.errored) != 0:
            sys.stderr.write(f" \033[31;1merrored={len(results.errored)}\033[0m")
        else:
            sys.stderr.write(f" errored={len(results.errored)}")

        sys.stderr.write("\n")
        sys.stderr.flush()
