import os
import sqlite3
import tempfile
import unittest

# Импортируем репозиторий (предполагается, что ваш код лежит в файле main.py)
from zametki import NoteRepository


class TestNoteRepository(unittest.TestCase):

    def setUp(self):
        """Подготовка: создаем временную БД перед каждым тестом."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.repo = NoteRepository(db_path=self.db_path)

    def tearDown(self):
        """Очистка: закрываем все связи и удаляем временную БД."""
        # 1. Удаляем объект репозитория, чтобы освободить файл базы данных
        if hasattr(self, 'repo'):
            del self.repo

            # 2. Закрываем дескриптор временного файла
        os.close(self.db_fd)

        # 3. Теперь файл свободен, и Windows разрешит его удалить
        try:
            os.unlink(self.db_path)
        except PermissionError:
            pass  # На случай, если ОС освобождает файл с небольшой задержкой

    def test_create_note_defaults(self):
        """TC-A1: Проверка создания заметки с параметрами по умолчанию."""
        note_id = self.repo.create_note()

        self.assertIsNotNone(note_id)
        # Проверяем, что в базу записались верные дефолты
        note = self.repo.get_note_by_id(note_id)
        self.assertEqual(note[0], "Новая заметка")  # title
        self.assertEqual(note[1], "Общее")  # category
        self.assertEqual(note[2], "")  # content

    def test_update_note(self):
        """TC-A2: Проверка полного обновления данных заметки."""
        note_id = self.repo.create_note()

        # Обновляем данные
        result = self.repo.update_note(
            note_id, "План на день", "Работа", "Купить молоко"
        )
        self.assertTrue(result)

        # Считываем из БД и проверяем точечно
        updated_note = self.repo.get_note_by_id(note_id)
        self.assertEqual(updated_note[0], "План на день")
        self.assertEqual(updated_note[1], "Работа")
        self.assertEqual(updated_note[2], "Купить молоко")

    def test_delete_note(self):
        """TC-A3: Проверка удаления существующей записи."""
        note_id = self.repo.create_note()

        # Удаляем
        delete_result = self.repo.delete_note(note_id)
        self.assertTrue(delete_result)

        # Проверяем, что поиск по ID возвращает None
        note_after_delete = self.repo.get_note_by_id(note_id)
        self.assertIsNone(note_after_delete)


def get_all_notes(self, query=""):
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    if query:
        # Приводим и поля в базе, и поисковый запрос к нижнему регистру
        sql = """SELECT id, title, category, content FROM notes 
                 WHERE LOWER(title) LIKE LOWER(?) 
                 OR LOWER(category) LIKE LOWER(?) 
                 OR LOWER(content) LIKE LOWER(?)"""
        wildcard = f"%{query}%"
        cursor.execute(sql, (wildcard, wildcard, wildcard))
    else:
        cursor.execute("SELECT id, title, category, content FROM notes")

    notes = cursor.fetchall()
    conn.close()
    return notes