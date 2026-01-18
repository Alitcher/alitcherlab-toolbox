import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path
import sys

# Path to core script
CORE_SCRIPT = Path(__file__).resolve().parents[1] / "core" / "yle_subs_fi_en.py"


class YleSubsUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Finnish Listening Study - Yle Subtitles")
        self.root.geometry("720x520")

        tk.Label(
            root,
            text="Yle Areena URL or urls.txt",
            font=("Segoe UI", 11, "bold")
        ).pack(pady=6)

        self.entry = tk.Entry(root, width=90)
        self.entry.pack(pady=4)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=6)

        tk.Button(
            btn_frame,
            text="Browse urls.txt",
            command=self.browse_file
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="Run",
            command=self.run_script,
            bg="#2ecc71"
        ).pack(side=tk.LEFT, padx=5)

        self.log = scrolledtext.ScrolledText(
            root,
            width=90,
            height=22,
            font=("Consolas", 9)
        )
        self.log.pack(padx=10, pady=10)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select urls.txt",
            filetypes=[("Text files", "*.txt")]
        )
        if file_path:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, file_path)

    def run_script(self):
        target = self.entry.get().strip()

        if not target:
            messagebox.showwarning(
                "Missing input",
                "Please paste a Yle URL or select urls.txt"
            )
            return

        if not CORE_SCRIPT.exists():
            messagebox.showerror(
                "Error",
                f"Core script not found:\n{CORE_SCRIPT}"
            )
            return

        self.log.insert(tk.END, f"Running: {target}\n\n")
        self.log.see(tk.END)

        try:
            process = subprocess.Popen(
                [sys.executable, str(CORE_SCRIPT), target],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="cp1252",   # Windows-safe
                errors="replace"     # Never crash on weird chars
            )

            for line in process.stdout:
                self.log.insert(tk.END, line)
                self.log.see(tk.END)

        except Exception as e:
            messagebox.showerror("Execution error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = YleSubsUI(root)
    root.mainloop()
