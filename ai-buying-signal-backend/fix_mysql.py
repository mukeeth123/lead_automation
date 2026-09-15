import os
import re

models_dir = "app/models"
for filename in os.listdir(models_dir):
    if filename.endswith(".py"):
        path = os.path.join(models_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replace mapped_column(String, ...) with mapped_column(String(255), ...)
        # Also handle mapped_column(String) -> mapped_column(String(255))
        content = re.sub(r'mapped_column\(String(?:(?![0-9]))', r'mapped_column(String(255)', content)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
print("Updated String to String(255) in models")
