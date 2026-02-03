"""
FastText model training management command.

Usage:
  python manage.py train_fasttext
  python manage.py train_fasttext --dim 300 --epoch 20
  python manage.py train_fasttext --include-menu-data --augment
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.nlp.services.fasttext_matcher import FastTextMatcher
from apps.nlp.services.training_utils import (
    augment_training_data,
    prepare_training_data,
    validate_training_data,
)


class Command(BaseCommand):
    help = "Train FastText model for menu matching"

    def add_arguments(self, parser):
        parser.add_argument("--dim", type=int, default=200, help="Vector dimension")
        parser.add_argument("--epoch", type=int, default=10, help="Epochs")
        parser.add_argument("--lr", type=float, default=0.05, help="Learning rate")
        parser.add_argument("--word-ngrams", type=int, default=2, help="Word n-grams")
        parser.add_argument(
            "--model-type",
            type=str,
            default="skipgram",
            choices=["skipgram", "cbow"],
            help="Model type",
        )
        parser.add_argument("--thread", type=int, default=4, help="Threads")
        parser.add_argument("--output", type=str, default=None, help="Output model path")
        parser.add_argument(
            "--training-data", type=str, default=None, help="Training data path"
        )
        parser.add_argument(
            "--include-menu-data",
            action="store_true",
            help="Include Menu model data",
        )
        parser.add_argument("--augment", action="store_true", help="Augment data")
        parser.add_argument(
            "--skip-data-prep",
            action="store_true",
            help="Use existing training file",
        )
        parser.add_argument(
            "--validate-only",
            action="store_true",
            help="Only validate training data",
        )

    def handle(self, *args, **options):
        project_root = getattr(settings, "PROJECT_ROOT", settings.BASE_DIR)
        training_data_path = options["training_data"] or str(
            project_root / "data" / "training_data.txt"
        )
        output_path = options["output"] or str(project_root / "models" / "menu.bin")

        self.stdout.write("FastText training pipeline")
        self.stdout.write("=" * 50)

        if options["validate_only"]:
            try:
                stats = validate_training_data(training_data_path)
                self.stdout.write(
                    f"Lines: {stats['line_count']}, avg: {stats['avg_length']}, "
                    f"range: {stats['min_length']}-{stats['max_length']}"
                )
            except FileNotFoundError as e:
                raise CommandError(f"Training data not found: {e}") from e
            return

        if not options["skip_data_prep"]:
            self.stdout.write("Step 1: Preparing training data...")
            try:
                count = prepare_training_data(
                    training_data_path,
                    include_menu_data=options["include_menu_data"],
                    project_root=project_root,
                )
                self.stdout.write(self.style.SUCCESS(f"Prepared {count} samples"))
            except Exception as e:
                raise CommandError(f"Prepare failed: {e}") from e

            if options["augment"]:
                augmented_path = training_data_path.replace(".txt", "_augmented.txt")
                try:
                    count = augment_training_data(training_data_path, augmented_path)
                    training_data_path = augmented_path
                    self.stdout.write(self.style.SUCCESS(f"Augmented to {count}"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Augment failed: {e}"))

            try:
                stats = validate_training_data(training_data_path)
                self.stdout.write(
                    f"Validate: {stats['line_count']} lines, "
                    f"avg {stats['avg_length']} chars"
                )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Validate: {e}"))
        else:
            if not os.path.exists(training_data_path):
                raise CommandError(f"Training data not found: {training_data_path}")

        self.stdout.write("Step 2: Training model...")
        try:
            matcher = FastTextMatcher()
            matcher.train_model(
                training_data_path=training_data_path,
                output_path=output_path,
                model_type=options["model_type"],
                dim=options["dim"],
                epoch=options["epoch"],
                lr=options["lr"],
                word_ngrams=options["word_ngrams"],
                thread=options["thread"],
            )
            self.stdout.write(self.style.SUCCESS("Training completed"))
        except Exception as e:
            raise CommandError(f"Training failed: {e}") from e

        self.stdout.write("Step 3: Validating model...")
        try:
            info = matcher.get_model_info()
            if info and info.get("is_loaded"):
                self.stdout.write(
                    f"Path: {info['model_path']}, "
                    f"vocab: {info['vocabulary_size']}, dim: {info['vector_dimension']}"
                )
                for q in ["치킨", "짜장면", "김치찌개"]:
                    vec = matcher.get_vector(q)
                    self.stdout.write(f"  {q}: {'ok' if vec is not None else 'fail'}")
            else:
                self.stdout.write(self.style.WARNING("Model load check failed"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Validate: {e}"))

        self.stdout.write("=" * 50)
        self.stdout.write(f"Model: {output_path}")
        self.stdout.write("Restart server to load new model.")
