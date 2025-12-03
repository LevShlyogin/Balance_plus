from gitlab_adapter import gitlab_client
from datetime import datetime

def main():
    print("--- Тест записи в GitLab ---")
    
    # Генерируем уникальный текст, чтобы каждый раз был новый коммит
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_name = "system_check/connection_log.txt"
    content = f"Проверка связи Оркестратора с GitLab.\nВремя проверки: {timestamp}\nСтатус: УСПЕХ."
    message = f"System: Automated check at {timestamp}"

    print(f"Пытаемся записать в файл: {file_name}")
    print(f"Сообщение коммита: {message}")

    try:
        commit = gitlab_client.create_commit(
            file_path=file_name,
            content=content,
            commit_message=message,
            branch='develop' # Убедитесь, что ветка называется main (или master)
        )
        
        print("\n✅ УСПЕХ! Коммит создан.")
        print(f"Hash: {commit.id}")
        print(f"Автор: {commit.author_name}")
        print(f"Ссылка: {commit.web_url}")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: Не удалось создать коммит.")
        print(e)

if __name__ == "__main__":
    main()