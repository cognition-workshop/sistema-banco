from rest_framework.throttling import UserRateThrottle


class PixTransferThrottle(UserRateThrottle):
    rate = '20/hour'
