class Task():
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def execute(self):
        # In real one use logs instead of prints, but for simplicity we use prints here
        print(f"Executing task: {self.name}")
        print(f"Description: {self.description}")