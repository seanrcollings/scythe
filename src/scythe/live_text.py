from arc.ui.utils import clear, home_pos


class LiveText:
    def __init__(self, initial: str):
        self.text = initial

    def __enter__(self):
        print("\033c")
        return self

    def __exit__(self, *args, **kwargs):
        print("\033c")

    def update(self, text):
        if text != self.text:
            self.text = text
            self.render()

    def render(self):
        print("\033c")
        home_pos()
        print(self.text)
