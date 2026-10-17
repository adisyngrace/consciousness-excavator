import sys
from src import http
r = http.get(sys.argv[1])
print(r["status"], r["content_type"], len(r["text"]))
print(r["text"] if len(sys.argv) > 2 else r["text"][:3000])
