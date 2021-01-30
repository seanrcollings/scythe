from .selection_menu import clear, home_pos


class LiveText:
    def __init__(self, initial: str):
        self.text = initial
        self.render()

    def update(self, text: str):
        self.text = text
        self.render()

    def render(self):
        clear()
        home_pos()
        print(self.text)
