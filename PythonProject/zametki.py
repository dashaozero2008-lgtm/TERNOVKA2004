import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk


class NoteRepository:
    """Класс для управления доступом к данным (Data Access Layer)."""

    def __init__(self, db_path="notes_app.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Инициализирует структуру базы данных."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        content TEXT,
                        category TEXT DEFAULT 'Общее'
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror(
                "Ошибка БД",
                f"Не удалось инициализировать базу данных: {e}"
            )

    def get_all_notes(self, query=None):
        """Возвращает список заметок с фильтрацией или без."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if query:
                    search_param = f"%{query.lower()}%"
                    cursor.execute(
                        """SELECT id, title, category FROM notes 
                           WHERE LOWER(title) LIKE ? 
                           OR LOWER(category) LIKE ? 
                           OR LOWER(content) LIKE ?""",
                        (search_param, search_param, search_param),
                    )
                else:
                    cursor.execute("SELECT id, title, category FROM notes")
                return cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror(
                "Ошибка БД",
                f"Не удалось загрузить список заметок: {e}"
            )
            return []

    def get_note_by_id(self, note_id):
        """Получает полные данные одной заметки по её ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT title, category, content "
                    "FROM notes WHERE id = ?",
                    (note_id,),
                )
                return cursor.fetchone()
        except sqlite3.Error as e:
            messagebox.showerror(
                "Ошибка БД",
                f"Не удалось загрузить заметку: {e}"
            )
            return None

    def create_note(self, title="Новая заметка", content="", category="Общее"):
        """Создает новую пустую заметку и возвращает её ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO notes (title, content, category) "
                    "VALUES (?, ?, ?)",
                    (title, content, category),
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            messagebox.showerror(
                "Ошибка БД",
                f"Не удалось создать заметку: {e}"
            )
            return None

    def update_note(self, note_id, title, category, content):
        """Обновляет существующую заметку."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE notes SET title = ?, category = ?, "
                    "content = ? WHERE id = ?",
                    (title, category, content, note_id),
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            messagebox.showerror(
                "Ошибка БД",
                f"Не удалось сохранить изменения: {e}"
            )
            return False

    def delete_note(self, note_id):
        """Удаляет заметку по ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM notes WHERE id = ?",
                    (note_id,),
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            messagebox.showerror(
                "Ошибка БД",
                f"Не удалось удалить заметку: {e}"
            )
            return False


class NotesApp:
    """Класс интерфейса приложения (Presentation & Business Logic Layer)."""

    def __init__(self, root, repository):
        self.root = root
        self.repo = repository

        self.root.title("Умные Заметки")
        self.root.geometry("900x600")

        self.current_note_id = None

        self.setup_ui()
        self.load_notes_list()

    def setup_ui(self):
        """Конструирует графический интерфейс приложения."""
        main_paned = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # --- ЛЕВАЯ ПАНЕЛЬ ---
        left_frame = ttk.Frame(main_paned, width=250)
        main_paned.add(left_frame, weight=1)

        # Поиск
        search_frame = ttk.LabelFrame(left_frame, text=" Поиск и Фильтр ")
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        self.search_var = tk.StringVar()
        self.search_var.trace_add(
            "write", lambda *args: self.load_notes_list()
        )
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, padx=5, pady=5)

        # Список заметок
        list_frame = ttk.LabelFrame(left_frame, text=" Список заметок ")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.notes_tree = ttk.Treeview(
            list_frame,
            columns=("title", "category"),
            show="headings",
            selectmode="browse",
        )
        self.notes_tree.heading("title", text="Название")
        self.notes_tree.heading("category", text="Категория/Тег")
        self.notes_tree.column("title", width=150)
        self.notes_tree.column("category", width=80)
        self.notes_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.notes_tree.bind("<<TreeviewSelect>>", self.on_note_select)

        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.notes_tree.yview
        )
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.notes_tree.configure(yscrollcommand=scrollbar.set)

        # Кнопки управления списком
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        new_btn = ttk.Button(
            btn_frame, text="Новая заметка", command=self.create_new_note
        )
        new_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        del_btn = ttk.Button(
            btn_frame, text="Удалить", command=self.delete_note
        )
        del_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)

        # --- СПРАВА: РЕДАКТОР ---
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)

        # Метаданные (Название и Категория)
        meta_frame = ttk.Frame(right_frame)
        meta_frame.pack(fill=tk.X, padx=5, pady=5)

        # Говорим сетке grid, что вторая колонка (индекс 1) должна расширяться
        meta_frame.columnconfigure(1, weight=1)

        ttk.Label(meta_frame, text="Название:").grid(
            row=0, column=0, sticky=tk.W, padx=2
        )
        self.title_entry = ttk.Entry(meta_frame, font=("Arial", 11))
        # Исправлено: заменено fill/expand на sticky="ew"
        self.title_entry.grid(
            row=0, column=1, sticky="ew", padx=2, pady=2
        )

        ttk.Label(meta_frame, text="Тег/Категория:").grid(
            row=1, column=0, sticky=tk.W, padx=2
        )
        self.cat_entry = ttk.Entry(meta_frame, font=("Arial", 11))
        # Исправлено: заменено fill/expand на sticky="ew"
        self.cat_entry.grid(
            row=1, column=1, sticky="ew", padx=2, pady=2
        )

        # Панель форматирования
        tools_frame = ttk.Frame(right_frame)
        tools_frame.pack(fill=tk.X, padx=5, pady=2)

        b_btn = ttk.Button(
            tools_frame,
            text="B (Жирный)",
            command=lambda: self.toggle_format("bold"),
        )
        b_btn.pack(side=tk.LEFT, padx=2)

        i_btn = ttk.Button(
            tools_frame,
            text="I (Курсив)",
            command=lambda: self.toggle_format("italic"),
        )
        i_btn.pack(side=tk.LEFT, padx=2)

        u_btn = ttk.Button(
            tools_frame,
            text="U (Подчеркнутый)",
            command=lambda: self.toggle_format("underline"),
        )
        u_btn.pack(side=tk.LEFT, padx=2)

        save_btn = ttk.Button(
            tools_frame,
            text="Сохранить изменения",
            command=self.save_current_note,
        )
        save_btn.pack(side=tk.RIGHT, padx=2)

        # Поле текста с поддержкой форматирования
        self.text_editor = tk.Text(
            right_frame, wrap=tk.WORD, font=("Arial", 12), undo=True
        )
        self.text_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Настройка тегов форматирования
        self.text_editor.tag_configure("bold", font=("Arial", 12, "bold"))
        self.text_editor.tag_configure("italic", font=("Arial", 12, "italic"))
        self.text_editor.tag_configure(
            "underline", font=("Arial", 12, "underline")
        )

    def load_notes_list(self):
        """Обновляет дерево элементов списка."""
        for item in self.notes_tree.get_children():
            self.notes_tree.delete(item)

        query = self.search_var.get().strip()
        rows = self.repo.get_all_notes(query if query else None)

        for row in rows:
            self.notes_tree.insert(
                "", tk.END, iid=row[0], values=(row[1], row[2])
            )

    def on_note_select(self, event):
        """Событие выбора заметки в списке."""
        selected = self.notes_tree.selection()
        if not selected:
            return

        self.current_note_id = int(selected[0])
        note = self.repo.get_note_by_id(self.current_note_id)

        if note:
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, note[0])
            self.cat_entry.delete(0, tk.END)
            self.cat_entry.insert(0, note[1])
            self.text_editor.delete("1.0", tk.END)
            self.text_editor.insert("1.0", note[2])

    def create_new_note(self):
        """Создает новую запись в системе."""
        new_id = self.repo.create_note()
        if new_id is not None:
            self.load_notes_list()
            self.notes_tree.selection_set(new_id)

    def save_current_note(self):
        """Считывает данные с полей UI и сохраняет текущую заметку."""
        if not self.current_note_id:
            messagebox.showwarning(
                "Внимание",
                "Выберите или создайте заметку для сохранения!"
            )
            return

        title = self.title_entry.get()
        category = self.cat_entry.get()
        content = self.text_editor.get("1.0", tk.END).strip()

        if self.repo.update_note(
                self.current_note_id, title, category, content
        ):
            active_id = self.current_note_id
            self.load_notes_list()
            self.notes_tree.selection_set(active_id)
            messagebox.showinfo("Успех", "Заметка сохранена!")

    def delete_note(self):
        """Удаляет текущую активную заметку."""
        if not self.current_note_id:
            return

        if messagebox.askyesno(
                "Удаление",
                "Вы уверены, что хотите удалить эту заметку?"
        ):
            if self.repo.delete_note(self.current_note_id):
                self.current_note_id = None
                self.title_entry.delete(0, tk.END)
                self.cat_entry.delete(0, tk.END)
                self.text_editor.delete("1.0", tk.END)
                self.load_notes_list()

    def toggle_format(self, tag):
        """Применяет Жирный/Курсив/Подчеркнутый к выделенному тексту."""
        try:
            start = self.text_editor.index("sel.first")
            end = self.text_editor.index("sel.last")

            current_tags = self.text_editor.tag_names(start)
            if tag in current_tags:
                self.text_editor.tag_remove(tag, start, end)
            else:
                self.text_editor.tag_add(tag, start, end)
        except tk.TclError:
            messagebox.showinfo(
                "Форматирование",
                "Сначала выделите текст мышкой!"
            )


if __name__ == "__main__":
    note_repository = NoteRepository()
    root = tk.Tk()
    app = NotesApp(root, note_repository)
    root.mainloop()



