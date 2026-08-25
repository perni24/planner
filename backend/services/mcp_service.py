from db.repositories import mcp_repo
from validators.request_validator import validate_text


MAX_BULK_AREAS = 50


def bulk_insert_area(names: list[str]) -> dict:
    if not names:
        raise ValueError("Inserire almeno un'area.")

    if len(names) > MAX_BULK_AREAS:
        raise ValueError(
            f"Puoi creare al massimo {MAX_BULK_AREAS} aree."
        )

    validated_names = []

    for name in names:
        validated_name, error = validate_text(name, "name")

        if error:
            raise ValueError(error)

        validated_names.append(validated_name)

    normalized_names = [name.casefold() for name in validated_names]

    if len(normalized_names) != len(set(normalized_names)):
        raise ValueError("La richiesta contiene nomi duplicati.")

    inserted_ids = mcp_repo.bulk_insert_area(validated_names)

    return {
        "requested": len(validated_names),
        "created": len(inserted_ids),
        "area_ids": inserted_ids,
    }
