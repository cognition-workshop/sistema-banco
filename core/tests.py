import time
from django.test import TestCase
from django.core.cache import cache


class RedisCacheTest(TestCase):
    """Test Redis cache functionality"""
    
    def setUp(self):
        """Clear cache before each test"""
        cache.clear()
    
    def tearDown(self):
        """Clear cache after each test"""
        cache.clear()
    
    def test_cache_set_and_get(self):
        """Test setting and getting values from cache"""
        cache.set('test_key', 'test_value')
        self.assertEqual(cache.get('test_key'), 'test_value')
    
    def test_cache_get_nonexistent_key(self):
        """Test getting a nonexistent key returns None"""
        self.assertIsNone(cache.get('nonexistent_key'))
    
    def test_cache_get_with_default(self):
        """Test getting a nonexistent key with default value"""
        self.assertEqual(cache.get('nonexistent_key', 'default'), 'default')
    
    def test_cache_delete(self):
        """Test deleting a key from cache"""
        cache.set('test_key', 'test_value')
        cache.delete('test_key')
        self.assertIsNone(cache.get('test_key'))
    
    def test_cache_add(self):
        """Test adding a key only if it doesn't exist"""
        self.assertTrue(cache.add('test_key', 'value1'))
        self.assertFalse(cache.add('test_key', 'value2'))
        self.assertEqual(cache.get('test_key'), 'value1')
    
    def test_cache_clear(self):
        """Test clearing all cache"""
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.clear()
        self.assertIsNone(cache.get('key1'))
        self.assertIsNone(cache.get('key2'))
    
    def test_cache_timeout(self):
        """Test cache expiration with timeout"""
        cache.set('timeout_key', 'value', timeout=1)
        self.assertEqual(cache.get('timeout_key'), 'value')
        time.sleep(2)
        self.assertIsNone(cache.get('timeout_key'))
    
    def test_cache_timeout_none(self):
        """Test cache with no timeout (permanent)"""
        cache.set('permanent_key', 'value', timeout=None)
        self.assertEqual(cache.get('permanent_key'), 'value')
    
    def test_cache_dict(self):
        """Test caching dictionary objects"""
        test_dict = {'key1': 'value1', 'key2': 'value2'}
        cache.set('dict_key', test_dict)
        cached_dict = cache.get('dict_key')
        self.assertEqual(cached_dict, test_dict)
    
    def test_cache_list(self):
        """Test caching list objects"""
        test_list = [1, 2, 3, 4, 5]
        cache.set('list_key', test_list)
        cached_list = cache.get('list_key')
        self.assertEqual(cached_list, test_list)
    
    def test_cache_has_key(self):
        """Test checking if key exists in cache"""
        cache.set('test_key', 'value')
        self.assertTrue(cache.has_key('test_key'))
        self.assertFalse(cache.has_key('nonexistent_key'))
    
    def test_cache_get_many(self):
        """Test getting multiple keys at once"""
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')
        result = cache.get_many(['key1', 'key2', 'key3'])
        self.assertEqual(result, {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'})
    
    def test_cache_set_many(self):
        """Test setting multiple keys at once"""
        data = {'key1': 'value1', 'key2': 'value2'}
        cache.set_many(data)
        self.assertEqual(cache.get('key1'), 'value1')
        self.assertEqual(cache.get('key2'), 'value2')
    
    def test_cache_delete_many(self):
        """Test deleting multiple keys at once"""
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.delete_many(['key1', 'key2'])
        self.assertIsNone(cache.get('key1'))
        self.assertIsNone(cache.get('key2'))
    
    def test_cache_uses_separate_database(self):
        """Test that cache uses Redis database 1 (separate from Celery db 0)"""
        from django_redis import get_redis_connection
        
        redis_conn = get_redis_connection("default")
        connection_kwargs = redis_conn.connection_pool.connection_kwargs
        self.assertEqual(connection_kwargs.get('db'), 1)
    
    def test_cache_connection(self):
        """Test Redis cache connection is working"""
        cache.set('connection_test', 'working')
        result = cache.get('connection_test')
        self.assertEqual(result, 'working')
