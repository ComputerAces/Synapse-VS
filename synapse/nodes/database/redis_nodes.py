from synapse.core.super_node import SuperNode
from synapse.nodes.registry import NodeRegistry
from synapse.core.types import DataType
from synapse.core.dependencies import DependencyManager
from synapse.nodes.lib.provider_node import ProviderNode

# Lazy Global
redis = None

def ensure_redis():
    global redis
    if redis: return True
    if DependencyManager.ensure("redis"):
        import redis as _r; redis = _r; return True
    return False

@NodeRegistry.register("Redis Provider", "Database/Redis")
class RedisProviderNode(ProviderNode):
    """
    Provides a connection to a Redis server for key-value storage and pub/sub.
    
    Inputs:
    - Flow: Execution trigger.
    - Host: Redis server hostname or IP.
    - Port: Redis server port (default 6379).
    - Password: Authentication password.
    - DB: Database index (default 0).
    
    Outputs:
    - Flow: Triggered when the provider is initialized.
    - Connected: True if connection was successful.
    """
    version = "2.1.0"
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.provider_type = "REDIS"
        self.properties["Host"] = "localhost"
        self.properties["Port"] = 6379
        self.properties["DB"] = 0
        self.properties["Password"] = ""
        self.client = None

    def define_schema(self):
        super().define_schema()
        self.input_schema.update({
            "Host": DataType.STRING,
            "Port": DataType.INTEGER,
            "Password": DataType.STRING,
            "DB": DataType.INTEGER
        })
        self.output_schema.update({
            "Flow": DataType.FLOW,
            "Error Flow": DataType.FLOW,
            "Connected": DataType.BOOLEAN
        })

    def start_scope(self, **kwargs):
        if not ensure_redis():
            self.logger.error("Redis module not installed.")
            self.bridge.set(f"{self.node_id}_Connected", False, self.name)
            return False

        host = kwargs.get("Host") or self.properties.get("Host", "localhost")
        port = int(kwargs.get("Port") or self.properties.get("Port", 6379))
        password = kwargs.get("Password") or self.properties.get("Password", "")
        db = int(kwargs.get("DB") or self.properties.get("DB", 0))

        try:
            self.client = redis.Redis(
                host=host, 
                port=port, 
                db=db, 
                password=password if password else None,
                decode_responses=True
            )
            
            if self.client.ping():
                self.logger.info(f"Connected to Redis at {host}:{port}")
                self.bridge.set(f"{self.node_id}_Connected", True, self.name)
                return super().start_scope(**kwargs)
            else:
                self.logger.error("Redis Ping failed.")
                self.bridge.set(f"{self.node_id}_Connected", False, self.name)
                return False

        except Exception as e:
            self.logger.error(f"Redis Connection Error: {e}")
            self.bridge.set(f"{self.node_id}_Connected", False, self.name)
            return False

    def register_provider_context(self):
        if self.client:
            self.bridge.set(f"{self.node_id}_Connected", True, self.name)


from synapse.core.super_node import SuperNode

class BaseRedisNode(SuperNode):
    """
    Base class for Redis operation nodes.
    
    Required Provider:
    - Redis: Provides client connectivity.
    """
    version = "2.1.0"
    required_providers = ["REDIS"]

    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)

    def get_redis_client(self):
        provider_id = self.get_provider_id("REDIS")
        if provider_id:
            return self.bridge.get(f"{provider_id}_Provider")
            
        return None

@NodeRegistry.register("Redis Set", "Database/Redis")
class RedisSetNode(BaseRedisNode):
    """
    Stores a value in Redis with an optional time-to-live (TTL).
    
    Inputs:
    - Flow: Execution trigger.
    - Key: The name of the key to set.
    - Value: The data to store.
    - TTL: Time to live in seconds (optional).
    
    Outputs:
    - Flow: Triggered after the set is successful.
    - Success: True if the operation succeeded.
    """
    version = "2.1.0"
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Key"] = ""
        self.properties["TTL"] = -1
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Key": DataType.STRING,
            "Value": DataType.ANY,
            "TTL": DataType.NUMBER
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Success": DataType.BOOLEAN
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_set)

    def handle_set(self, Key=None, Value=None, TTL=None, **kwargs):
        client = self.get_redis_client()
        if not client:
            self.logger.error("No Redis Provider found.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        key = Key if Key is not None else kwargs.get("Key") or self.properties.get("Key", "")
        if not key:
            self.logger.error("Key is required.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        val = str(Value) if Value is not None else ""
        ttl_val = TTL if TTL is not None else kwargs.get("TTL") or self.properties.get("TTL", -1)
        ttl = int(ttl_val)
        
        try:
            if ttl > 0:
                client.set(key, val, ex=ttl)
            else:
                client.set(key, val)
            self.bridge.set(f"{self.node_id}_Success", True, self.name)
        except Exception as e:
            self.logger.error(f"Redis Set Error: {e}")
            self.bridge.set(f"{self.node_id}_Success", False, self.name)
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Redis Get", "Database/Redis")
class RedisGetNode(BaseRedisNode):
    """
    Retrieves a value from Redis by its key.
    
    Inputs:
    - Flow: Execution trigger.
    - Key: The name of the key to fetch.
    
    Outputs:
    - Flow: Triggered after the retrieval.
    - Value: The data fetched from Redis.
    - Found: True if the key exists.
    """
    version = "2.1.0"
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Key"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Key": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Value": DataType.STRING,
            "Found": DataType.BOOLEAN
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_get)

    def handle_get(self, Key=None, **kwargs):
        client = self.get_redis_client()
        if not client:
            self.logger.error("No Redis Provider found.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        key = Key if Key is not None else kwargs.get("Key") or self.properties.get("Key", self.properties.get("Key", ""))
        if not key:
            self.logger.error("Key is required.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True

        try:
            val = client.get(key)
            if val is not None:
                self.bridge.set(f"{self.node_id}_Value", val, self.name)
                self.bridge.set(f"{self.node_id}_Found", True, self.name)
            else:
                self.bridge.set(f"{self.node_id}_Value", None, self.name)
                self.bridge.set(f"{self.node_id}_Found", False, self.name)
        except Exception as e:
            self.logger.error(f"Redis Get Error: {e}")
            self.bridge.set(f"{self.node_id}_Found", False, self.name)
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Redis Delete", "Database/Redis")
class RedisDeleteNode(BaseRedisNode):
    """
    Removes a key and its value from Redis.
    
    Inputs:
    - Flow: Execution trigger.
    - Key: The name of the key to delete.
    
    Outputs:
    - Flow: Triggered after deletion.
    - Success: True if the deletion command was sent successfully.
    """
    version = "2.1.0"
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Key"] = ""
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Key": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Success": DataType.BOOLEAN
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_delete)

    def handle_delete(self, Key=None, **kwargs):
        client = self.get_redis_client()
        if not client:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        key = Key if Key is not None else kwargs.get("Key") or self.properties.get("Key", self.properties.get("Key", ""))
        if not key:
            self.logger.error("Key is required.")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
        try:
            client.delete(key)
            self.bridge.set(f"{self.node_id}_Success", True, self.name)
        except Exception as e:
            self.logger.error(f"Redis Delete Error: {e}")
            self.bridge.set(f"{self.node_id}_Success", False, self.name)
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Redis Keys", "Database/Redis")
class RedisKeysNode(BaseRedisNode):
    """
    Retrieves a list of keys matching a specified pattern.
    
    Inputs:
    - Flow: Execution trigger.
    - Pattern: Glob-style pattern (e.g., "user:*").
    
    Outputs:
    - Flow: Triggered after keys are listed.
    - Keys: List of matching key names.
    """
    version = "2.1.0"
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Pattern"] = "*"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Pattern": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Keys": DataType.LIST
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_keys)

    def handle_keys(self, Pattern=None, **kwargs):
        client = self.get_redis_client()
        if not client:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        pattern = Pattern if Pattern is not None else kwargs.get("Pattern") or self.properties.get("Pattern", self.properties.get("Pattern", "*"))
        try:
            keys = client.keys(pattern)
            self.bridge.set(f"{self.node_id}_Keys", keys, self.name)
        except Exception as e:
            self.logger.error(f"Redis Keys Error: {e}")
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Redis Publish", "Database/Redis")
class RedisPublishNode(BaseRedisNode):
    """
    Publishes a message to a Redis channel.
    
    Inputs:
    - Flow: Execution trigger.
    - Channel: The channel name.
    - Message: The string message to publish.
    
    Outputs:
    - Flow: Triggered after publishing.
    - Subscribers: Number of clients that received the message.
    """
    version = "2.1.0"
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Channel"] = "updates"
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Channel": DataType.STRING,
            "Message": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Subscribers": DataType.NUMBER
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_publish)

    def handle_publish(self, Channel=None, Message=None, **kwargs):
        client = self.get_redis_client()
        if not client:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        channel = Channel if Channel is not None else kwargs.get("Channel") or self.properties.get("Channel", self.properties.get("Channel", "updates"))
        message = str(Message) if Message is not None else ""
        
        try:
            count = client.publish(channel, message)
            self.bridge.set(f"{self.node_id}_Subscribers", count, self.name)
        except Exception as e:
            self.logger.error(f"Redis Publish Error: {e}")
            
        self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        return True

@NodeRegistry.register("Redis Subscribe", "Database/Redis")
class RedisSubscribeNode(BaseRedisNode):
    """
    Subscribes to a Redis channel and triggers Flow for each received message.
    
    Inputs:
    - Flow: Execution trigger.
    - Channel: The channel name to watch.
    
    Outputs:
    - Flow: Triggered for every new message.
    - Message: The content of the received message.
    - Channel: The channel where the message originated.
    """
    version = "2.1.0"
    
    def __init__(self, node_id, name, bridge):
        super().__init__(node_id, name, bridge)
        self.properties["Channel"] = "updates"
        self.is_service = True
        self.define_schema()
        self.register_handlers()

    def define_schema(self):
        self.input_schema = {
            "Flow": DataType.FLOW,
            "Channel": DataType.STRING
        }
        self.output_schema = {
            "Flow": DataType.FLOW,
            "Message": DataType.STRING,
            "Source Channel": DataType.STRING
        }

    def register_handlers(self):
        self.register_handler("Flow", self.handle_subscribe)

    def handle_subscribe(self, Channel=None, **kwargs):
        client = self.get_redis_client()
        if not client:
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
            return True
            
        channel = Channel if Channel is not None else kwargs.get("Channel") or self.properties.get("Channel", self.properties.get("Channel", "updates"))
        self.logger.info(f"Subscribing to '{channel}'...")
        
        try:
            pubsub = client.pubsub()
            pubsub.subscribe(channel)
            self.bridge.set(f"{self.node_id}_IsServiceRunning", True, self.name)
            
            for message in pubsub.listen():
                if message['type'] == 'message':
                    data = message['data']
                    src_channel = message['channel']
                    self.bridge.set(f"{self.node_id}_Message", data, self.name)
                    self.bridge.set(f"{self.node_id}_Source Channel", src_channel, self.name)
                    self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        except Exception as e:
            self.logger.error(f"Redis Subscribe Error: {e}")
            self.bridge.set(f"{self.node_id}_ActivePorts", ["Flow"], self.name)
        finally:
            self.bridge.set(f"{self.node_id}_IsServiceRunning", False, self.name)
        return True
