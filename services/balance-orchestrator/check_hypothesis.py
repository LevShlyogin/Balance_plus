from gitlab_adapter import gitlab_client

def main():
    print("--- 1. Проверка соединения ---")
    status = gitlab_client.check_connection()
    print(status)
    
    if "Ошибка" in status:
        print("Прерываем выполнение из-за ошибки подключения.")
        return

    print("\n--- 2. Получение списка проектов ---")
    projects = gitlab_client.list_projects(limit=10)
    
    if not projects:
        print("Проектов не найдено. Создайте хотя бы один пустой проект в GitLab.")
        return

    print(f"Найдено проектов: {len(projects)}")
    for p in projects:
        print(f"ID: {p.id} | Name: {p.name} | URL: {p.http_url_to_repo}")

    # Берем первый попавшийся проект для теста чтения файлов
    target_project = projects[0]
    print(f"\n--- 3. Чтение файлов из проекта ID: {target_project.id} ({target_project.name}) ---")
    
    # Пытаемся угадать ветку (обычно main или master)
    branch = target_project.default_branch or 'main'
    print(f"Используем ветку: {branch}")

    files = gitlab_client.list_repository_files(target_project.id, ref=branch)
    
    if files:
        print("Содержимое корня репозитория:")
        for f in files:
            icon = "📁" if f['type'] == 'tree' else "📄"
            print(f"{icon} {f['name']} ({f['path']})")
    else:
        print("Файлов не найдено или ошибка доступа к дереву.")

if __name__ == "__main__":
    main()
    