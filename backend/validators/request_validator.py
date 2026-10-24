SQLITE_MAX_INTEGER = 2**63 - 1


def validate_int(value, field_name):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None, f"{field_name} must be a valid integer"

    try:
        value = int(value)
    except (TypeError, ValueError):
        return None, f"{field_name} must be a valid integer"

    if value <= 0:
        return None, f"{field_name} must be greater than 0"

    if value > SQLITE_MAX_INTEGER:
        return None, f"{field_name} must be less than or equal to {SQLITE_MAX_INTEGER}"

    return value, None


def validate_text(value, field_name, required=True):
    if value is None:
        if required:
            return None, f"{field_name} is required"
        return "", None

    if not isinstance(value, str):
        return None, f"{field_name} must be a string"

    value = value.strip()

    if required and not value:
        return None, f"{field_name} cannot be empty"

    return value, None


def validate_payload(data, fields):
    validated = {}

    for field in fields:
        match field:
            case "id" | "area_id" | "project_id" | "task_id":
                value, error = validate_int(data.get(field), field)

            case "name" | "title":
                value, error = validate_text(data.get(field), field)

            case "description":
                value, error = validate_text(data.get(field), field, required=False)

            case "parent_id":
                value = data.get(field)
                if value is not None:
                    value, error = validate_int(value, field)
                    if error:
                        return None, error
                validated[field] = value
                continue

            case _:
                return None, f"Unknown field: {field}"

        if error:
            return None, error

        validated[field] = value

    return validated, None
