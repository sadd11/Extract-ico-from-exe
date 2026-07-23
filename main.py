import os
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image

import win32gui
import win32ui
import win32con

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


def extract_icon_pil(exe_path: str, size: int = 64) -> Image.Image | None:
    """Извлекает иконку из EXE заданной ширины/высоты в формате PIL Image."""
    try:
        large_icons, _ = win32gui.ExtractIconEx(exe_path, 0)
        if not large_icons:
            return None

        hicon = large_icons[0]

        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbitmap = win32ui.CreateBitmap()
        hbitmap.CreateCompatibleBitmap(hdc, size, size)

        hdc_mem = hdc.CreateCompatibleDC()
        hdc_mem.SelectObject(hbitmap)

        win32gui.DrawIconEx(
            hdc_mem.GetSafeHdc(),
            0, 0,
            hicon,
            size, size,
            0, None,
            win32con.DI_NORMAL
        )

        bmp_info = hbitmap.GetInfo()
        bmp_str = hbitmap.GetBitmapBits(True)

        img = Image.frombuffer(
            'RGBA',
            (bmp_info['bmWidth'], bmp_info['bmHeight']),
            bmp_str, 'raw', 'BGRA', 0, 1
        )

        win32gui.DestroyIcon(hicon)
        hdc_mem.DeleteDC()
        hdc.DeleteDC()
        win32gui.DeleteObject(hbitmap.GetHandle())

        return img
    except Exception as e:
        print(f"Ошибка при извлечении: {e}")
        return None


class IconExtractorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("EXE Icon Extractor")
        self.geometry("520x480")
        self.resizable(False, False)

        self.exe_path = ""
        self.extracted_img = None

        self._build_ui()

    def _build_ui(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=12)
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Заголовок
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Извлечение иконки из EXE",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=(15, 10))

        # Выбор EXE файла
        self.file_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.file_frame.pack(pady=5)

        self.path_entry = ctk.CTkEntry(
            self.file_frame,
            placeholder_text="Выберите .exe файл...",
            width=320
        )
        self.path_entry.pack(side="left", padx=(0, 10))

        self.btn_browse = ctk.CTkButton(
            self.file_frame,
            text="Обзор...",
            command=self.browse_file,
            width=90
        )
        self.btn_browse.pack(side="right")

        # Блок настроек (Формат и Размер)
        self.settings_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.settings_frame.pack(pady=10)

        # Переключатель формата
        self.format_label = ctk.CTkLabel(self.settings_frame, text="Формат:", font=ctk.CTkFont(weight="bold"))
        self.format_label.pack(side="left", padx=(0, 5))

        self.format_var = ctk.StringVar(value="PNG")
        self.format_seg_btn = ctk.CTkSegmentedButton(
            self.settings_frame,
            values=["PNG", "ICO"],
            variable=self.format_var
        )
        self.format_seg_btn.pack(side="left", padx=(0, 20))

        # Выбор размера
        self.size_label = ctk.CTkLabel(self.settings_frame, text="Размер:", font=ctk.CTkFont(weight="bold"))
        self.size_label.pack(side="left", padx=(0, 5))

        self.size_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            values=["16x16", "32x32", "48x48", "64x64", "128x128", "256x256"],
            command=self.on_size_change,
            width=100
        )
        self.size_menu.set("64x64")
        self.size_menu.pack(side="left")

        # Превью иконки
        self.preview_frame = ctk.CTkFrame(self.main_frame, width=120, height=120, corner_radius=8)
        self.preview_frame.pack(pady=10)
        self.preview_frame.pack_propagate(False)

        self.preview_label = ctk.CTkLabel(self.preview_frame, text="Нет иконки")
        self.preview_label.pack(expand=True)

        # Кнопка сохранения
        self.btn_save = ctk.CTkButton(
            self.main_frame,
            text="Сохранить иконку",
            command=self.save_icon,
            state="disabled",
            fg_color="#2FA572",
            hover_color="#1E7A52",
            height=36,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.btn_save.pack(pady=(10, 15))

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Выберите исполняемый файл",
            filetypes=[("Исполняемые файлы", "*.exe"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.exe_path = file_path
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, file_path)
            self.load_preview()

    def get_selected_size(self) -> int:
        return int(self.size_menu.get().split('x')[0])

    def on_size_change(self, choice):
        if self.exe_path:
            self.load_preview()

    def load_preview(self):
        size = self.get_selected_size()
        img = extract_icon_pil(self.exe_path, size=size)
        if img:
            self.extracted_img = img
            # Отображение в превью с максимальным размером 96x96
            preview_render_size = min(size, 96)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(preview_render_size, preview_render_size))
            self.preview_label.configure(image=ctk_img, text="")
            self.btn_save.configure(state="normal")
        else:
            self.extracted_img = None
            self.preview_label.configure(image="", text="Не найдено")
            self.btn_save.configure(state="disabled")

    def save_icon(self):
        if not self.extracted_img:
            return

        chosen_format = self.format_var.get().lower()
        default_name = os.path.splitext(os.path.basename(self.exe_path))[0] + "_icon"

        if chosen_format == "ico":
            file_types = [("ICO Icon", "*.ico")]
            ext = ".ico"
        else:
            file_types = [("PNG Image", "*.png")]
            ext = ".png"

        save_path = filedialog.asksaveasfilename(
            title="Сохранить иконку как...",
            initialfile=default_name,
            defaultextension=ext,
            filetypes=file_types
        )

        if save_path:
            try:
                if chosen_format == "ico":
                    # Сохранение со стандартным набором размеров для качественного ICO
                    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
                    self.extracted_img.save(save_path, format="ICO", sizes=ico_sizes)
                else:
                    self.extracted_img.save(save_path, format="PNG")

                messagebox.showinfo("Успех", f"Иконка успешно сохранена в формате {chosen_format.upper()}:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")


if __name__ == "__main__":
    app = IconExtractorApp()
    app.mainloop()
