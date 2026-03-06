"""DrugBank interaction extraction."""

import csv
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from loguru import logger

from .constants import (
    ACCEPTED_IDENTIFIER_TYPES,
    DRUGBANK_NS,
    DRUGBANK_XML_FILE,
    UNKNOWN_VALUE,
    InteractionCSVColumns,
    generate_identifier_column_name,
)


class DrugBankInteractionsExtractor:
    """Extract drug interactions from DrugBank XML database."""

    def __init__(self, xml_file: Path | None = None):
        """Initialize extractor with XML file path."""
        self.xml_file = xml_file or DRUGBANK_XML_FILE
        self.drug_identifiers_map: dict[str, dict[str, str | None]] = {}

    @staticmethod
    def _get_external_identifiers(drug_elem: ET.Element) -> dict[str, str | None]:
        """Extract external identifiers from a drug element based on accepted types."""
        identifiers: dict[str, str | None] = {
            identifier_type.value: None for identifier_type in ACCEPTED_IDENTIFIER_TYPES
        }

        external_ids = drug_elem.find(f"{DRUGBANK_NS}external-identifiers")
        if external_ids is not None:
            for ext_id in external_ids.findall(f"{DRUGBANK_NS}external-identifier"):
                resource_elem = ext_id.find(f"{DRUGBANK_NS}resource")
                identifier_elem = ext_id.find(f"{DRUGBANK_NS}identifier")
                if resource_elem is not None and identifier_elem is not None:
                    resource = resource_elem.text
                    identifier = identifier_elem.text
                    if resource in identifiers:
                        identifiers[resource] = identifier

        return identifiers

    def _build_identifiers_map(self, max_drugs: int | None = None) -> None:
        """First pass: Build complete map of DrugBank IDs to external identifiers."""
        logger.info("Building DrugBank ID to identifier mapping...")
        drug_count = 0

        context = ET.iterparse(str(self.xml_file), events=("end",))  # noqa: S314
        context = iter(context)
        _, _root = next(context)

        for _event, elem in context:
            if elem.tag == f"{DRUGBANK_NS}drug":
                drug_count += 1

                if max_drugs and drug_count > max_drugs:
                    break

                if drug_count % 500 == 0:
                    logger.info(f"Processed {drug_count} drugs for identifier mapping")

                drugbank_id_elem = elem.find(f"{DRUGBANK_NS}drugbank-id")
                drugbank_id = (
                    drugbank_id_elem.text if drugbank_id_elem is not None else None
                )

                if drugbank_id:
                    drug_identifiers = self._get_external_identifiers(elem)
                    self.drug_identifiers_map[drugbank_id] = drug_identifiers

                elem.clear()

        logger.info(f"Built identifier map for {len(self.drug_identifiers_map)} drugs")

    def parse_interactions(
        self, max_drugs: int | None = None, build_map_first: bool = True
    ) -> list[dict[str, str | None]]:
        """Parse drug interactions from XML.

        Args:
            max_drugs: Maximum number of drugs to process (for testing)
            build_map_first: If True, do a first pass to build complete identifier map
        """
        if build_map_first and not self.drug_identifiers_map:
            self._build_identifiers_map(max_drugs=max_drugs)

        interactions = []
        drug_count = 0

        context = ET.iterparse(str(self.xml_file), events=("end",))  # noqa: S314
        context = iter(context)
        _, _root = next(context)

        for _event, elem in context:
            if elem.tag == f"{DRUGBANK_NS}drug":
                drug_count += 1

                if max_drugs and drug_count > max_drugs:
                    break

                if drug_count % 500 == 0:
                    logger.info(
                        f"Processed {drug_count} drugs, found {len(interactions)} interactions"
                    )

                name_elem = elem.find(f"{DRUGBANK_NS}name")
                drug_name = name_elem.text if name_elem is not None else UNKNOWN_VALUE

                drugbank_id_elem = elem.find(f"{DRUGBANK_NS}drugbank-id")
                drugbank_id = (
                    drugbank_id_elem.text if drugbank_id_elem is not None else None
                )

                # Get identifiers for drug 1 (current drug)
                drug_identifiers = self.drug_identifiers_map.get(drugbank_id or "", {})
                if not build_map_first and drugbank_id:
                    # If not building map first, extract on the fly
                    drug_identifiers = self._get_external_identifiers(elem)
                    self.drug_identifiers_map[drugbank_id] = drug_identifiers

                interactions_elem = elem.find(f"{DRUGBANK_NS}drug-interactions")
                if interactions_elem is not None:
                    for drug_interaction in interactions_elem.findall(
                        f"{DRUGBANK_NS}drug-interaction"
                    ):
                        name_elem = drug_interaction.find(f"{DRUGBANK_NS}name")
                        interacting_drug_name = (
                            name_elem.text if name_elem is not None else None
                        )

                        interacting_drugbank_id_elem = drug_interaction.find(
                            f"{DRUGBANK_NS}drugbank-id"
                        )
                        interacting_drugbank_id = (
                            interacting_drugbank_id_elem.text
                            if interacting_drugbank_id_elem is not None
                            else None
                        )

                        description_elem = drug_interaction.find(
                            f"{DRUGBANK_NS}description"
                        )
                        description = (
                            description_elem.text
                            if description_elem is not None
                            else ""
                        )

                        if interacting_drug_name and drug_name:
                            # Get identifiers for drug 2 (interacting drug)
                            # This will work because we built the map in first pass
                            interacting_identifiers: dict[str, str | None] = (
                                self.drug_identifiers_map.get(
                                    interacting_drugbank_id or "", {}
                                )
                            )

                            interaction_record = {
                                InteractionCSVColumns.DRUG_1.value: drug_name,
                                InteractionCSVColumns.DRUG_1_DRUGBANK_ID.value: drugbank_id,
                                InteractionCSVColumns.DRUG_2.value: interacting_drug_name,
                                InteractionCSVColumns.DRUG_2_DRUGBANK_ID.value: interacting_drugbank_id,
                                InteractionCSVColumns.INTERACTION_DESCRIPTION.value: description,
                            }

                            # Add identifier columns dynamically
                            for drug_num, identifiers in [
                                (1, drug_identifiers),
                                (2, interacting_identifiers),
                            ]:
                                for identifier_type in ACCEPTED_IDENTIFIER_TYPES:
                                    column_name = generate_identifier_column_name(
                                        drug_num, identifier_type
                                    )
                                    interaction_record[column_name] = identifiers.get(
                                        identifier_type.value
                                    )

                            interactions.append(interaction_record)

                elem.clear()

        return interactions

    def save_interactions_to_csv(
        self, interactions: list[dict[str, str | None]], output_path: Path
    ) -> None:
        """Save already-parsed interactions to CSV."""
        if output_path.exists():
            output_path.unlink()
            logger.debug(f"Deleted existing file: {output_path.name}")

        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = InteractionCSVColumns.get_all_columns()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(interactions)
        logger.info(f"Saved {len(interactions)} interactions to {output_path.name}")

    def extract_to_csv(
        self,
        output_path: Path,
        max_drugs: int | None = None,
        build_map_first: bool = True,
    ) -> list[dict[str, str | None]]:
        """Extract interactions and save to CSV.

        Args:
            output_path: Path to save CSV file
            max_drugs: Maximum number of drugs to process (for testing)
            build_map_first: If True, do a first pass to build complete identifier map
                            This ensures Drug 2 RxCUI is available even if it appears later in XML
        """
        logger.info(f"Parsing {self.xml_file.name}")

        interactions = self.parse_interactions(
            max_drugs=max_drugs, build_map_first=build_map_first
        )

        logger.info(f"Found {len(interactions)} interactions")

        self.save_interactions_to_csv(interactions, output_path)
        return interactions

    def analyze_interactions(self, interactions: list[dict[str, str | None]]) -> None:
        """Analyze and display interaction statistics."""
        if not interactions:
            logger.warning("No interactions found")
            return

        drug_interaction_counts = defaultdict(int)
        for interaction in interactions:
            drug_interaction_counts[
                interaction.get(InteractionCSVColumns.DRUG_1.value, UNKNOWN_VALUE)
            ] += 1

        sorted_drugs = sorted(
            drug_interaction_counts.items(), key=lambda x: x[1], reverse=True
        )

        top_drugs = "\n".join(
            f"  {i}. {drug}: {count}"
            for i, (drug, count) in enumerate(sorted_drugs[:10], 1)
        )

        sample_interactions = []
        for i, interaction in enumerate(interactions[:5], 1):
            drug1 = interaction.get(InteractionCSVColumns.DRUG_1.value, UNKNOWN_VALUE)
            drug2 = interaction.get(InteractionCSVColumns.DRUG_2.value, UNKNOWN_VALUE)
            desc = interaction.get(InteractionCSVColumns.INTERACTION_DESCRIPTION.value)
            desc_short = desc[:150] if desc else ""
            sample_interactions.append(
                f"{i}. {drug1} <-> {drug2}"
                + (f"\n   {desc_short}..." if desc_short else "")
            )

        logger.info(
            f"Interaction analysis:\n"
            f"  Total interactions: {len(interactions)}\n"
            f"  Drugs with interactions: {len(drug_interaction_counts)}\n"
            f"  Top 10 drugs by interactions:\n{top_drugs}\n"
            f"  Sample interactions:\n" + "\n".join(sample_interactions)
        )
