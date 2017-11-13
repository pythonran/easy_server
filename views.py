from view_core import View
from easyserver import easyResponse
import json

class Index(View):
    def get(self, request):
        print request
        data = {
            "body": request.body,
            "option": "test"
        }
        return easyResponse(json.dumps(data))
