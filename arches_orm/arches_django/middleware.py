from arches_orm.adapter import get_adapter

class ArchesORMContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        with get_adapter().context(user=request.user):
            response = self.get_response(request)
        return response

class ArchesORMContextFreeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        with get_adapter().context_free():
            response = self.get_response(request)
        return response
