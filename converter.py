import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import webbrowser
from PIL import Image
import shutil
from pathlib import Path
import subprocess
from pillow_heif import register_heif_opener

register_heif_opener()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("High Quality Media Converter")
        self.geometry("600x850")

        if hasattr(sys, '_MEIPASS'):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(".").absolute()

        icon_path = base_path / "logo.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        self.configure(bg="#ECE9D8")
        self._setup_styles()
        self._setup_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        xp_font = ("Tahoma", 9)

        style.configure("XP.Horizontal.TProgressbar",
                        troughcolor='#D4D0C8', background='#0054E3',
                        bordercolor='#7A96DF', lightcolor='#3C8EF3', darkcolor='#0054E3')

        style.configure("XP.TButton", font=xp_font, background="#ECE9D8",
                        foreground="black", borderwidth=2, relief="raised")
        style.map("XP.TButton", background=[('active', '#E3F4FF')], relief=[('pressed', 'sunken')])

    def _setup_ui(self):
        title_frame = tk.Frame(self, bg="#0054E3", height=30)
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="Media Converter", font=("Tahoma", 10, "bold"),
                 bg="#0054E3", fg="white", padx=10).pack(side="left")

        content_frame = tk.Frame(self, bg="#ECE9D8", padx=20, pady=10)
        content_frame.pack(fill="both", expand=True)

        mode_frame = tk.LabelFrame(content_frame, text=" MP4 Encoding Settings ",
                                   font=("Tahoma", 8, "bold"), bg="#ECE9D8", padx=10, pady=10)
        mode_frame.pack(fill="x", pady=5)

        self.encoder_var = tk.StringVar(value="h264_nvenc")
        for text, val in [("CPU (libx264)", "libx264"),
                          ("GPU (NVIDIA NVENC)", "h264_nvenc"),
                          ("GPU (Intel QSV)", "h264_qsv")]:
            tk.Radiobutton(mode_frame, text=text, variable=self.encoder_var, value=val,
                           bg="#ECE9D8", font=("Tahoma", 9), activebackground="#ECE9D8").pack(anchor="w")

        self._create_section(content_frame, "PNG", "#e3f2fd")
        self._create_section(content_frame, "JPG", "#f1f8e9")
        self._create_section(content_frame, "MP4", "#fff3e0")

        progress_frame = tk.Frame(content_frame, bg="#ECE9D8")
        progress_frame.pack(pady=10, fill="x")

        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal",
                                            length=400, mode="determinate", maximum=100,
                                            style="XP.Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x", pady=5)

        self.percentage_label = tk.Label(progress_frame, text="Ready", font=("Tahoma", 9), bg="#ECE9D8")
        self.percentage_label.pack()

        tk.Label(content_frame, text="Process Log:", font=("Tahoma", 9, "bold"), bg="#ECE9D8").pack(pady=(5, 0), anchor="w")
        self.log_area = scrolledtext.ScrolledText(content_frame, width=70, height=10, state='disabled',
                                                  bg="#FFFFFF", fg="black", font=("Tahoma", 8),
                                                  relief="sunken", borderwidth=2)
        self.log_area.pack(pady=5, fill="both", expand=True)

        footer_frame = tk.Frame(content_frame, bg="#ECE9D8")
        footer_frame.pack(fill="x", side="bottom", pady=5)

        self.status_label = tk.Label(footer_frame, text="Idle", fg="#7A96DF", font=("Tahoma", 9), bg="#ECE9D8")
        self.status_label.pack(side="left")

        credit_frame = tk.Frame(footer_frame, bg="#ECE9D8")
        credit_frame.pack(side="right")
        tk.Label(credit_frame, text="Created by ", font=("Tahoma", 9), bg="#ECE9D8").pack(side="left")

        link_label = tk.Label(credit_frame, text="Aki", font=("Tahoma", 9, "underline"),
                              bg="#ECE9D8", fg="#0054E3", cursor="hand2")
        link_label.pack(side="left")
        link_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/Irony-s9c"))

    def _create_section(self, parent, fmt, bg_color):
        frame = tk.LabelFrame(parent, text=f" Convert to {fmt} ", font=("Tahoma", 9, "bold"),
                              bg=bg_color, relief="groove")
        frame.pack(fill="x", pady=5, ipady=5)

        tk.Button(frame, text=f"Select Files to Convert to {fmt}", width=35, height=2,
                  command=lambda f=fmt: self._start_process(f),
                  font=("Tahoma", 9), bg="#ECE9D8", relief="raised", borderwidth=2,
                  activebackground="#E3F4FF").pack(pady=5)

    def _set_progress(self, val):
        self.progress_bar["value"] = val

    def _set_status(self, text, color="black"):
        self.status_label.config(text=text, fg=color)

    def _set_label(self, text):
        self.percentage_label.config(text=text)

    def _log(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')

    def _start_process(self, target_fmt):
        input_paths = filedialog.askopenfilenames(title="Select files")
        if not input_paths:
            return
        output_dir = filedialog.askdirectory(title="Select Destination")
        if not output_dir:
            return

        self.progress_bar["value"] = 0
        self.status_label.config(text="Starting...", fg="#0054E3")

        thread = threading.Thread(target=self._run_conversion, args=(input_paths, target_fmt, Path(output_dir)))
        thread.daemon = True
        thread.start()

    def _run_conversion(self, input_paths, target_fmt, target_dir):
        success_count = 0
        paths = [Path(p).resolve() for p in input_paths]
        total_size = sum(p.stat().st_size for p in paths) or 1
        done_size = 0
        total_files = len(paths)
        encoder = self.encoder_var.get()

        for i, path in enumerate(paths, 1):
            file_size = path.stat().st_size
            base_pct = (done_size / total_size) * 100
            weight = (file_size / total_size) * 100

            self.after(0, self._set_status, f"Processing {i}/{total_files}: {path.name}", "#0054E3")

            if target_fmt == "MP4":
                result = self._convert_video_with_progress(path, target_dir, base_pct, weight, encoder)
            else:
                result = self._convert_logic(path, target_fmt, target_dir)

            if result:
                success_count += 1

            done_size += file_size
            self.after(0, self._set_progress, (done_size / total_size) * 100)

        self.after(0, self._set_progress, 100)
        self.after(0, self._set_status, f"Done: {success_count}/{total_files} converted.", "#008000")
        self.after(0, self._set_label, "Completed")
        self.after(0, self._log, f"--- Batch done: {success_count}/{total_files} succeeded ---")

    def _get_duration(self, file_path):
        try:
            flags = 0x08000000 if os.name == 'nt' else 0
            ffprobe = shutil.which("ffprobe") or "ffprobe"
            cmd = [ffprobe, '-v', 'error', '-show_entries', 'format=duration',
                   '-of', 'default=noprint_wrappers=1:nokey=1', str(file_path)]
            res = subprocess.check_output(cmd, stderr=subprocess.STDOUT, creationflags=flags)
            return float(res.decode().strip())
        except Exception:
            return 0

    def _convert_video_with_progress(self, file_path, out_dir, base_pct, weight, encoder):
        output_file = out_dir / f"{file_path.stem}.mp4"
        duration = self._get_duration(file_path)
        ffmpeg = shutil.which("ffmpeg") or "ffmpeg"

        cmd = [
            ffmpeg, '-y',
            '-i', str(file_path),
            '-vcodec', encoder,
            '-pix_fmt', 'yuv420p',
            '-map', '0:v:0',
            '-map', '0:a?',
            '-ac', '2',
            '-acodec', 'aac',
            '-strict', 'experimental',
            '-f', 'mp4',
        ]

        if encoder == 'libx264':
            cmd.extend(['-crf', '17', '-preset', 'veryslow'])
        elif encoder == 'h264_nvenc':
            cmd.extend(['-cq', '19', '-preset', 'p7'])
        elif encoder == 'h264_qsv':
            cmd.extend(['-global_quality', '20', '-preset', 'veryslow'])

        cmd.extend(['-progress', 'pipe:1', '-nostats', str(output_file)])

        startupinfo = None
        creation_flags = 0
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creation_flags = 0x08000000

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       universal_newlines=True, encoding='utf-8', errors='ignore',
                                       bufsize=1, startupinfo=startupinfo, creationflags=creation_flags)
            while True:
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        break
                    continue
                if "out_time_ms=" in line:
                    try:
                        us = int(line.split('=')[1].strip())
                        if duration > 0:
                            pct = min(base_pct + (us / 1_000_000 / duration) * weight,
                                      base_pct + weight - 0.01)
                            self.after(0, self._set_progress, pct)
                    except (ValueError, IndexError):
                        pass
            process.wait()
            ok = process.returncode == 0
            self.after(0, self._log, f"[{'OK' if ok else 'ERROR'}] {file_path.name}")
            return ok
        except Exception as e:
            self.after(0, self._log, f"[ERROR] {file_path.name}: {e}")
            return False

    def _convert_logic(self, file_path, target_fmt, out_dir):
        try:
            output_file = out_dir / f"{file_path.stem}.{target_fmt.lower()}"
            ext = file_path.suffix.lower()

            if ext in ['.cr3', '.cr2', '.nef', '.arw']:
                import rawpy
                with rawpy.imread(str(file_path)) as raw:
                    rgb = raw.postprocess(use_camera_wb=True)
                img = Image.fromarray(rgb)
            else:
                img = Image.open(str(file_path))

            with img:
                if target_fmt == "JPG":
                    img.convert("RGB").save(str(output_file), "JPEG", quality=100, subsampling=0)
                else:
                    img.save(str(output_file), "PNG", compress_level=0)

            self.after(0, self._log, f"[OK] {file_path.name}")
            return True
        except Exception as e:
            self.after(0, self._log, f"[ERROR] {file_path.name}: {e}")
            return False

if __name__ == "__main__":
    app = App()
    app.mainloop()
