from ipware import get_client_ip


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        client_ip, is_routable = get_client_ip(request)
        
        request.audit_ip = client_ip
        request.audit_channel = self._get_channel(request)
        request.audit_geolocation = self._get_geolocation(client_ip)
        
        response = self.get_response(request)
        return response

    def _get_channel(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif request.path.startswith('/api/'):
            return 'api'
        else:
            return 'web'

    def _get_geolocation(self, ip):
        if not ip:
            return None
        
        return f"IP: {ip}"
