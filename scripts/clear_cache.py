import redis

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Clear all keys
r.flushall()
print("Redis cache cleared")
