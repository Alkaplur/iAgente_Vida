import time
from langsmith import Client

client = Client()

print("Tus proyectos en LangSmith:")
for project in client.list_projects():
    print(project)

time.sleep(1)
