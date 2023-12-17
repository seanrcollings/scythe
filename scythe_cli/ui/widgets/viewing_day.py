from datetime import datetime, timedelta
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message


class ViewingDay(Widget):
    class Back(Message):
        ...

    viewing_day: reactive[datetime] = reactive(datetime.now)

    def render(self):
        content = self.viewing_day.strftime("%Y-%m-%d")

        if self.viewing_day.date() == datetime.now().date():
            content += " [grey35](Today)[/grey35]"
        else:
            content += " [blue][@click='back'](Back to Today)[/][/blue]"

        return content

    def action_back(self):
        self.post_message(self.Back())
