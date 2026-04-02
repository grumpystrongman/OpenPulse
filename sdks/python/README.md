# Python SDK

```python
from openpulse_sdk import OpenPulseClient

client = OpenPulseClient("http://localhost:8003")
print(client.observations(limit=10))
```
