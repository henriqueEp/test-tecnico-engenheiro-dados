from pathlib import Path
from typing import Any

import yaml
from pyspark.sql import DataFrame
from pyspark.sql.functions import col
from pyspark.sql.types import DecimalType, LongType, StringType

from app.utils.logger import get_logger

_log = get_logger("contract")

_TYPE_MAP: dict[str, Any] = {
    "long": LongType(),
    "string": StringType(),
}


def _parse_logical_type(logical_type: str) -> Any:
    lt = logical_type.strip().lower()
    if lt in _TYPE_MAP:
        return _TYPE_MAP[lt]
    if lt.startswith("decimal"):
        inner = lt[len("decimal"):].strip("() ")
        parts = inner.split(",")
        return DecimalType(int(parts[0].strip()), int(parts[1].strip()))
    raise ValueError(f"Tipo ODCS não suportado: {logical_type!r}")


def validate_contract(df: DataFrame, contract_path: str | Path) -> None:
    """Valida um DataFrame contra um contrato ODCS v3 (YAML).

    Estratégia WAP (Write → Audit → Publish):
      - Violações de schema  → ValueError imediato (hard stop)
      - Violações de quality → WARNING no log   (soft alert, pipeline continua)
    """
    contract_path = Path(contract_path)
    with contract_path.open(encoding="utf-8") as fh:
        contract: dict[str, Any] = yaml.safe_load(fh)

    name = contract.get("name", contract_path.stem)
    schema_models: list[dict] = contract.get("schema", [])
    quality_rules: list[dict] = contract.get("quality", [])

    # ── Audit: schema (hard) ────────────────────────────────────────────────
    errors: list[str] = []
    actual_fields = {f.name: f for f in df.schema.fields}

    for model in schema_models:
        for col_def in model.get("columns", []):
            col_name = col_def["name"]

            if col_name not in actual_fields:
                errors.append(f"coluna ausente: '{col_name}'")
                continue

            actual = actual_fields[col_name]
            expected_type = _parse_logical_type(col_def["logicalType"])

            if type(actual.dataType) is not type(expected_type):
                errors.append(
                    f"tipo incorreto em '{col_name}': "
                    f"esperado={expected_type.simpleString()}, "
                    f"encontrado={actual.dataType.simpleString()}"
                )

            expected_nullable = col_def.get("isNullable", True)
            if actual.nullable != expected_nullable:
                errors.append(
                    f"nullability incorreta em '{col_name}': "
                    f"esperado nullable={expected_nullable}, "
                    f"encontrado nullable={actual.nullable}"
                )

    if errors:
        bullet = "\n  • ".join(errors)
        raise ValueError(f"[contrato:{name}] Schema violado:\n  • {bullet}")

    _log.info(f"[contrato:{name}] Schema OK — {len(actual_fields)} coluna(s) validada(s)")

    # ── Audit: quality rules (soft) ─────────────────────────────────────────
    for rule in quality_rules:
        col_name = rule["column"]
        rule_type = rule["rule"]
        description = rule.get("description", "")

        if rule_type == "not_null":
            count = df.filter(col(col_name).isNull()).count()
            if count > 0:
                _log.warning(
                    f"[contrato:{name}] not_null violado em '{col_name}': "
                    f"{count:,} valor(es) nulo(s). {description}"
                )
            else:
                _log.info(f"[contrato:{name}] not_null OK em '{col_name}'")

        elif rule_type == "positive":
            count = df.filter(col(col_name).isNotNull() & (col(col_name) <= 0)).count()
            if count > 0:
                _log.warning(
                    f"[contrato:{name}] positive violado em '{col_name}': "
                    f"{count:,} valor(es) ≤ 0. {description}"
                )
            else:
                _log.info(f"[contrato:{name}] positive OK em '{col_name}'")

        else:
            _log.warning(f"[contrato:{name}] Regra desconhecida ignorada: '{rule_type}'")
