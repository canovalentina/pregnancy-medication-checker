"""DrugBank data exploration."""

import csv
from collections import defaultdict
from pathlib import Path

from loguru import logger

from .constants import DRUGBANK_DATA_DIR


class DrugBankExplorer:
    """Explore DrugBank dataset structure and available data files."""

    def __init__(self, data_dir: Path | None = None):
        """Initialize explorer with data directory."""
        self.data_dir = data_dir or DRUGBANK_DATA_DIR

    def explore_csv_files(self) -> None:
        """List and examine CSV files in the dataset."""
        csv_files = list(self.data_dir.rglob("*.csv"))
        logger.info(f"Found {len(csv_files)} CSV files")

        by_dir = defaultdict(list)
        for csv_file in csv_files:
            rel_path = csv_file.relative_to(self.data_dir)
            by_dir[rel_path.parent].append(rel_path.name)

        file_list = []
        for directory, files in sorted(by_dir.items()):
            file_list.append(f"{directory}/")
            for f in sorted(files):
                file_path = self.data_dir / directory / f
                size = file_path.stat().st_size
                file_list.append(f"  {f} ({size:,} bytes)")

                if "drug" in f.lower() or "interaction" in f.lower():
                    try:
                        with open(file_path, "r", encoding="utf-8") as csvfile:
                            reader = csv.reader(csvfile)
                            for i, row in enumerate(reader):
                                if i < 3:
                                    file_list.append(f"    {row[:5]}")
                                else:
                                    break
                    except Exception as e:
                        file_list.append(f"    Error reading {f}: {e}")

        if file_list:
            logger.info("\n".join(file_list))

    def check_interaction_data(self) -> None:
        """Check for drug interaction data sources."""
        drug_links = (
            self.data_dir / "External Links" / "External Drug Links" / "drug links.csv"
        )
        if drug_links.exists():
            with open(drug_links, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                row_count = sum(1 for _ in reader)
                logger.info(
                    f"{drug_links.name}\n"
                    f"  Rows: {row_count:,}\n"
                    f"  Columns: {', '.join(header[:10])}..."
                )

        vocab_file = self.data_dir / "Open Data" / "drugbank vocabulary.csv"
        if vocab_file.exists():
            with open(vocab_file, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                row_count = sum(1 for _ in reader)
                logger.info(f"{vocab_file.name}\n  Rows: {row_count:,}")

        xml_files = list(self.data_dir.rglob("*.xml"))
        if xml_files:
            xml_info = [f"XML files: {len(xml_files)}"]
            for xml_file in xml_files:
                size = xml_file.stat().st_size / (1024**3)
                xml_info.append(
                    f"  {xml_file.relative_to(self.data_dir)} ({size:.2f} GB)"
                )
            logger.info("\n".join(xml_info))

    def explore(self) -> None:
        """Run full exploration of the dataset."""
        if not self.data_dir.exists():
            logger.error(f"Data directory not found: {self.data_dir}")
            return

        logger.info(f"Base directory: {self.data_dir}")
        self.explore_csv_files()
        self.check_interaction_data()
