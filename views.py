from view_core import View
from easyserver import easyResponse

class Index(View):
    def get(self):
        return easyResponse("hello easyserver")
