import time
import sys


def truncated_value(val):
    if not isinstance(val, str) and not isinstance(val, bytes):
        return val
    elif len(val) < 100:
        return val
    else:
        return f"{val[0:100]}..."


class TaskLogger:
    def __init__(self, logger, task):
        self.logger = logger
        self.task = task
        self.colors = ["\033[1;36m", "\033[1;34m", "\033[1;35m"]

    def __enter__(self):
        self.start_time = time.time()
        line = "  " * self.logger.depth()
        line += self.colors[self.logger.depth() % len(self.colors)]
        line += f"> {self.task.name}"
        line += "\033[0m"
        for key, val in self.task.params.__dict__().items():
            line += f" {key}=\033[1m{truncated_value(val)}\033[0m"
        logger.info(line)

        self.logger.task_stack.append(self)

    def __exit__(self, exc, value, tb):
        self.logger.task_stack.pop()

        duration = time.time() - self.start_time
        line = "  " * self.logger.depth()
        line += self.colors[self.logger.depth() % len(self.colors)]
        line += f"< {self.task.name}"
        line += " \033[0m\033[3m ({0:.2f}s)\033[0m".format(duration)
        if exc:
            line += f" \033[31m✗\033[0m {exc.__name__} {value}"
        else:
            line += f" \033[32m✓\033[0m"
            if self.task.return_value:
                line += f" << {truncated_value(self.task.return_value)}"
        logger.info(line)


class CopyLogger:
    def __init__(self, logger, src, dest):
        self.logger = logger
        self.src = src
        self.dest = dest

    def __enter__(self):
        self.start_time = time.time()
        line = "  " * self.logger.depth()
        line += f"💾 Copying \033[1m{self.src}\033[0m ==> \033[1m{self.dest}\033[0m"
        self.logger.info(line)
        self.logger.task_stack.append(self)

    def __exit__(self, exc, tb, something):
        self.logger.task_stack.pop()
        duration = time.time() - self.start_time
        line = "  " * self.logger.depth()
        if exc:
            line += "\033[31m✗\033[0m copying failed ({0:.2f}s)".format(duration)
        else:
            line += "\033[32m✓\033[0m done copying ({0:.2f}s)".format(duration)
        self.logger.info(line)


class TestLogger:
    def __init__(self, logger, task, name):
        self.logger = logger
        self.task = task
        self.name = name

    def __enter__(self):
        self.start_time = time.time()
        line = "  " * self.logger.depth()
        line += f"🏃 Running {self.task.task_name} > \033[1m{self.name}\033[0m"
        self.logger.info(line)
        self.logger.task_stack.append(self)

    def __exit__(self, exc, tb, something):
        self.logger.task_stack.pop()
        duration = time.time() - self.start_time
        line = "  " * self.logger.depth()
        if exc:
            line += "\033[31m✗\033[0m test failed ({0:.2f}s)".format(duration)
        else:
            line += "\033[32m✓\033[0m test succeeded ({0:.2f}s)".format(duration)
        self.logger.info(line)


class Logger:
    def __init__(self, writer):
        self.writer = writer
        self.task_stack = []

    def with_task(self, task):
        return TaskLogger(self, task)

    def with_test(self, task, name):
        return TestLogger(self, task, name)

    def shell_start(self, context, command):
        line = "  " * len(self.task_stack)
        line += f"\033[33m${context.descriptor()}\033[0m {truncated_value(command)}"
        self.writer.write(line)
        self.writer.flush()

    def shell_stop(self, context, code, out, err):
        self.info(
            f" # code={code} out={truncated_value(out)} err={truncated_value(err)}"
        )

    def with_copy(self, src, dest):
        return CopyLogger(self, src, dest)

    def info(self, line):
        self.writer.write(line)
        self.writer.write("\n")
        self.writer.flush()

    def depth(self):
        return len(self.task_stack)


logger = Logger(sys.stderr)
