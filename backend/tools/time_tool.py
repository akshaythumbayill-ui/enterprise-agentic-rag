from datetime import datetime


class TimeTool:
    def run(self):
        now = datetime.now().astimezone()

        return {
            "answer": now.strftime("%A, %d %B %Y, %I:%M:%S %p %Z")
        }


time_tool = TimeTool()