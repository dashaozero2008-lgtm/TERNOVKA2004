import os
import sqlite3
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from zametki import NoteRepository, NotesApp


class TestNotesAppIntegration(unittest.TestCase):

    def setUp(self):
        """Инициализация окружения перед каждым тестом."""
        self.root = tk.Tk()
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.repo = NoteRepository(db_path=self.db_path)

        # Явно создаем таблицы в пустой временной БД, если этого не делает репозиторий
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, category TEXT, content TEXT)"
        )
        conn.close()

        self.app = NotesApp(self.root, self.repo)

    def tearDown(self):
        """Полная очистка и закрытие всех процессов Windows."""
        if hasattr(self, "root"):
            self.root.destroy()

        if hasattr(self, "app"):
            del self.app
        if hasattr(self, "repo"):
            del self.repo

        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except PermissionError:
            pass

    def test_create_new_note_ui_integration(self):
        """TC-INT-01: Проверка создания заметки через вызов UI-метода."""
        # Вызываем метод интерфейса
        self.app.create_new_note()

        # Если в приложении переменная называется self.active_note_id,
        # то и в тесте вместо current_note_id напишите active_note_id:
        self.assertIsNotNone(self.app.current_note_id)

    def test_save_current_note_integration(self):
        """TC-INT-02: Тест передачи данных из текстовых полей UI в базу данных."""
        # Шаг 1: Создаем активную заметку
        note_id = self.repo.create_note()
        self.app.current_note_id = note_id

        # Шаг 2: Имитируем ввод пользователя в текстовые поля UI
        self.app.title_entry.insert(0, "Новый Заголовок")
        self.app.cat_entry.insert(0, "Личное")
        self.app.text_editor.insert("1.0", "Текст тестовой заметки")

        # Шаг 3: Перехватываем окно "Успех" (чтобы оно не вылезало на экран) и сохраняем
        with patch("tkinter.messagebox.showinfo") as mock_info:
            self.app.save_current_note()
            mock_info.assert_called_once_with("Успех", "Заметка сохранена!")

        # Шаг 4: Проверяем, дошли ли данные до базы данных через репозиторий
        db_data = self.repo.get_note_by_id(note_id)
        self.assertEqual(db_data[0], "Новый Заголовок")
        self.assertEqual(db_data[2], "Текст тестовой заметки")

    # Имитируем, что в диалоговом окне подтверждения удаления пользователь нажал "Да" (True)
    @patch("tkinter.messagebox.askyesno", return_value=True)
    def test_delete_note_integration_confirm(self, mock_ask):
        """TC-INT-03: Проверка удаления при подтверждении в messagebox."""
        note_id = self.repo.create_note()
        self.app.current_note_id = note_id

        # Вызываем метод удаления
        self.app.delete_note()

        # Проверяем, что окно вопроса было вызвано
        mock_ask.assert_called_once()

        # Проверяем, что статус активной заметки сбросился, а из БД она исчезла
        self.assertIsNone(self.app.current_note_id)
        self.assertIsNone(self.repo.get_note_by_id(note_id))

    def test_save_note_without_selection(self):
        """TC-INT-06: Защита от сохранения, если ни одна заметка не выбрана."""
        self.app.current_note_id = None

        # Перехватываем предупреждение messagebox.showwarning
        with patch("tkinter.messagebox.showwarning") as mock_warning:
            self.app.save_current_note()
            # Проверяем, сработала ли защита UI
            mock_warning.assert_called_once_with(
                "Внимание", "Выберите или создайте заметку для сохранения!"
            )