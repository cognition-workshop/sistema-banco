from ipware import get_client_ip


class IPCaptureMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        client_ip, is_routable = get_client_ip(request)
        request.client_ip = client_ip if client_ip else 'unknown'
        
        response = self.get_response(request)
        return response
