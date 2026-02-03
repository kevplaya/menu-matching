# Docker Script Execution

Run these commands from the project root with containers up: `docker-compose up -d`.

## Server

```bash
# Start backend (migrate + runserver on 0.0.0.0:8000)
docker-compose up -d

# View logs
docker-compose logs -f web
```

## FastText Training

```bash
# Prepare training data (StandardMenu + data/sample_menus.csv + variants) and train model
docker-compose exec web python manage.py train_fasttext

# Include Menu table data and augment with space variants
docker-compose exec web python manage.py train_fasttext --include-menu-data --augment

# Custom paths and hyperparameters
docker-compose exec web python manage.py train_fasttext --dim 300 --epoch 20 --output /app/models/menu.bin

# Validate existing training data only (no training)
docker-compose exec web python manage.py train_fasttext --validate-only

# Use existing training file (skip data prep)
docker-compose exec web python manage.py train_fasttext --skip-data-prep
```

Trained model is written to `models/menu.bin` (mounted at `/app/models` in the container). Restart the web service to load the new model. If the process is killed (exit 137, OOM), try `--dim 100 --epoch 5` or increase Docker memory.

## Sample Data

```bash
# Create standard menus and sample menus (Django shell)
docker-compose exec web python manage.py shell -c "
from scripts.create_sample_data import create_standard_menus, create_sample_menus, print_statistics
create_standard_menus()
create_sample_menus()
print_statistics()
"

# Or run the script as main (requires PYTHONPATH or run from src)
docker-compose exec web bash -c "cd /app/src && python scripts/create_sample_data.py"
```

## Tests

```bash
# All tests
docker-compose exec web pytest

# With coverage
docker-compose exec web pytest --cov=apps

# Specific app or file
docker-compose exec web pytest src/apps/menus/tests/
docker-compose exec web pytest src/apps/menus/tests/test_matching.py -v
```

## Django Shell

```bash
# Interactive shell
docker-compose exec web python manage.py shell

# One-liner: test FastText matching
docker-compose exec web python manage.py shell -c "
from apps.menus.services import MenuMatchingService
svc = MenuMatchingService()
r = svc.find_standard_menu_by_fasttext('자장면')
print(r)
r = svc.find_standard_menu_by_fasttext('후라이드 치킨')
print(r)
"
```

## Migrations

```bash
# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate
```
