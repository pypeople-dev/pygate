"""
The contents of this file are property of pygate.org
Review the Apache License 2.0 for valid authorization of use
See https://github.com/pypeople-dev/pygate for more information
"""

# External imports
import requests

# Internal imports
from utils.database import db
from utils.cache import cache_manager
from services.cache import pygate_cache

class GatewayService:
    api_collection = db.apis
    endpoint_collection = db.endpoints

    @staticmethod
    async def gateway(request):
        """
        External gateway.
        """
        api = pygate_cache.get_cache('api_id_cache', request.path) or GatewayService.api_collection.find_one({'api_path': request.path})
        if not api:
            raise ValueError("API does not exists")
        endpoints = pygate_cache.get_cache('api_endpoint_cache', api.get('api_id')) or GatewayService.endpoint_collection.find({'api_id': api.get('api_id')})
        if not endpoints or request.path not in endpoints:
            raise ValueError("Endpoint does not exists")
        server = api.get('api_server')[0]
        url = server + request.path
        response = None
        if request.method == 'GET':
            response = requests.get(url)
        elif request.method == 'POST':
            response = requests.post(url, json=request.json)
        elif request.method == 'PUT':
            response = requests.put(url, json=request.json)
        elif request.method == 'DELETE':
            response = requests.delete(url)
        return response