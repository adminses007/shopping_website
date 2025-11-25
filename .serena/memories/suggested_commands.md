# Suggested Commands for Shopping Website Development

## Project Setup
```bash
cd /home/adminses/My_Projects/shopping_website
pip install -r requirements.txt
```

## Running the Application
```bash
python run.py
# or
python app.py
```

## Access Information
- **Website URL**: http://localhost:5000
- **Admin Account**: admin / admin123

## Development Commands
```bash
# Check Python syntax
python -m py_compile app.py

# Run tests (if available)
python test_*.py

# Check file permissions
ls -la

# Find files
find . -name "*.py" -type f
find . -name "*.html" -type f

# Search in files
grep -r "中文" templates/
grep -r "Chinese" templates/

# Database operations
sqlite3 shopping_website.db
.tables
.schema
```

## File Management
```bash
# List files
ls -la

# Copy files
cp source destination

# Move files
mv source destination

# Create directories
mkdir -p new_directory

# Remove files
rm filename
```

## Git Commands (if using version control)
```bash
git status
git add .
git commit -m "message"
git push
```