from modules.storage import load_categories, save_categories


def get_categories():
    return load_categories()


def add_category(name, color):
    name = name.strip()

    if not name:
        return False, "Kategorin måste ha ett namn."

    categories = load_categories()

    if any(
        category["name"].lower() == name.lower()
        for category in categories
    ):
        return False, "Kategorin finns redan."

    categories.append({
        "name": name,
        "color": color
    })

    save_categories(categories)

    return True, "Kategorin har lagts till."


def update_category(old_name, new_name, new_color):
    categories = load_categories()

    if not new_name.strip():
        return False, "Namnet får inte vara tomt."

    if any(
        category["name"].lower() == new_name.lower()
        and category["name"] != old_name
        for category in categories
    ):
        return False, "Kategorin finns redan."

    for category in categories:
        if category["name"] == old_name:
            category["name"] = new_name.strip()
            category["color"] = new_color
            break
    else:
        return False, "Kategorin kunde inte hittas."

    save_categories(categories)

    from modules.storage import load_tasks, save_tasks

    tasks = load_tasks()

    for task in tasks:
        if task.get("category") == old_name:
            task["category"] = new_name.strip()

    save_tasks(tasks)

    return True, "Kategorin har uppdaterats."


def delete_category(name):
    categories = load_categories()

    categories = [
        category for category in categories
        if category["name"] != name
    ]

    save_categories(categories)

    return True, "Kategorin har tagits bort."


def get_category_color(name):
    for category in load_categories():
        if category["name"] == name:
            return category.get("color", "#808080")

    return "#808080"