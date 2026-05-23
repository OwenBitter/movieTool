import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from core.scanner import Scanner
from core.classifier import Classifier
from core.copier import Copier
from core.metadata_fetcher import MetadataFetcher
from core.actress_fetcher import ActressFetcher


class MainWindow:
    def __init__(self, ctx):
        self.ctx = ctx
        self.config = ctx.config
        self.logger = ctx.logger
        self.excel = ctx.excel
        self.root = tk.Tk()
        self.root.title('电影自动化管理系统')
        self.root.geometry('920x680')
        self.root.minsize(820, 600)
        self._build_ui()

    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        config_frame = ttk.Frame(notebook)
        tools_frame = ttk.Frame(notebook)
        log_frame = ttk.Frame(notebook)

        notebook.add(config_frame, text='配置管理')
        notebook.add(tools_frame, text='操作工具')
        notebook.add(log_frame, text='日志输出')

        self._build_config_panel(config_frame)
        self._build_tools_panel(tools_frame)
        self._build_log_panel(log_frame)

        self.status_label = ttk.Label(self.root, text='就绪', anchor='w')
        self.status_label.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _build_config_panel(self, parent):
        frame = ttk.Frame(parent, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        self.download_var = tk.StringVar(value=self.config.get('path_config', {}).get('download_dir', ''))
        self.classify_var = tk.StringVar(value=self.config.get('path_config', {}).get('classify_dir', ''))
        self.excel_var = tk.StringVar(value=self.config.get('path_config', {}).get('excel_path', ''))
        self.copy_var = tk.StringVar(value=self.config.get('path_config', {}).get('copy_target_dir', ''))
        self.backup_var = tk.StringVar(value=self.config.get('path_config', {}).get('backup_dir', ''))

        labels = ['下载目录:', '分类目录:', 'Excel 路径:', '复制目标:', '备份目录:']
        vars_ = [self.download_var, self.classify_var, self.excel_var, self.copy_var, self.backup_var]

        for index, (label, var) in enumerate(zip(labels, vars_)):
            ttk.Label(frame, text=label).grid(row=index, column=0, sticky=tk.W, pady=6)
            ttk.Entry(frame, textvariable=var, width=72).grid(row=index, column=1, sticky=tk.W, padx=6)
            action = self._browse_file if index == 2 else self._browse_dir
            ttk.Button(frame, text='选择', width=10, command=lambda v=var, a=action: a(v)).grid(row=index, column=2, padx=6)

        save_button = ttk.Button(frame, text='保存配置', command=self._save_config)
        save_button.grid(row=6, column=1, pady=18, sticky=tk.E)
        ttk.Label(frame, text='保存后配置会写回 config.json 并立即生效。').grid(row=7, column=1, sticky=tk.W)

    def _build_tools_panel(self, parent):
        frame = ttk.Frame(parent, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        action_frame = ttk.LabelFrame(frame, text='快速操作', padding=10)
        action_frame.pack(fill=tk.X)

        actions = [
            ('初始化', self._init_excel),
            ('扫描', self._scan),
            ('女优查询', self._actress_lookup),
            ('分类', self._classify),
            ('复制', self._copy),
            ('备份', self._backup),
        ]
        for idx, (text, callback) in enumerate(actions):
            ttk.Button(action_frame, text=text, width=14, command=lambda fn=callback: self._run_task(fn)).grid(row=0, column=idx, padx=6, pady=6)

        search_frame = ttk.LabelFrame(frame, text='在线查询', padding=10)
        search_frame.pack(fill=tk.X, pady=10)

        ttk.Label(search_frame, text='影片名称/代码:').grid(row=0, column=0, sticky=tk.W)
        self.fetch_entry = ttk.Entry(search_frame, width=50)
        self.fetch_entry.grid(row=0, column=1, padx=6)
        ttk.Button(search_frame, text='元数据查询', width=14, command=lambda: self._run_task(self._fetch)).grid(row=0, column=2, padx=6)

        ttk.Label(search_frame, text='状态过滤:').grid(row=1, column=0, sticky=tk.W, pady=8)
        self.status_entry = ttk.Entry(search_frame, width=50)
        self.status_entry.grid(row=1, column=1, padx=6, pady=8)
        ttk.Button(search_frame, text='显示统计', width=14, command=lambda: self._run_task(self._show)).grid(row=1, column=2, padx=6)

        result_frame = ttk.LabelFrame(frame, text='执行结果', padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        self.result_text = scrolledtext.ScrolledText(result_frame, state='disabled', wrap=tk.WORD, font=('微软雅黑', 10), height=12)
        self.result_text.pack(fill=tk.BOTH, expand=True)

        progress_frame = ttk.Frame(frame)
        progress_frame.pack(fill=tk.X, pady=10)
        ttk.Label(progress_frame, text='进度:').pack(side=tk.LEFT)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=6)
        ttk.Button(progress_frame, text='清除日志', command=self._clear_log).pack(side=tk.RIGHT)

    def _build_log_panel(self, parent):
        frame = ttk.Frame(parent, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(frame, state='disabled', wrap=tk.WORD, font=('微软雅黑', 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _set_status(self, text):
        self.status_label.config(text=text)

    def _append_log(self, text):
        for widget in (self.log_text, self.result_text):
            widget.config(state='normal')
            widget.insert(tk.END, text + '\n')
            widget.see(tk.END)
            widget.config(state='disabled')

    def _clear_log(self):
        for widget in (self.log_text, self.result_text):
            widget.config(state='normal')
            widget.delete('1.0', tk.END)
            widget.config(state='disabled')

    def _set_progress(self, value):
        self.progress_var.set(value)
        if value > 0:
            self.progress_bar.configure(mode='determinate')
        self.root.update_idletasks()

    def _pulse_progress(self, stop_event):
        """Animate indeterminate progress while task runs."""
        self.root.after(0, lambda: self.progress_bar.configure(mode='indeterminate'))
        self.root.after(0, self.progress_bar.start)
        while not stop_event.is_set():
            stop_event.wait(0.1)
        self.root.after(0, self.progress_bar.stop)
        self.root.after(0, lambda: self.progress_bar.configure(mode='determinate'))

    def _run_task(self, target):
        self._set_status('执行中...')
        self._append_log('开始：' + target.__name__)
        self._set_progress(0)
        self._disable_buttons(True)
        stop_event = threading.Event()
        pulse_thread = threading.Thread(target=self._pulse_progress, args=(stop_event,), daemon=True)
        pulse_thread.start()
        thread = threading.Thread(target=self._task_wrapper, args=(target, stop_event), daemon=True)
        thread.start()

    def _disable_buttons(self, disabled):
        state = tk.DISABLED if disabled else tk.NORMAL

        def _recurse(parent):
            for child in parent.winfo_children():
                if isinstance(child, (tk.Button, ttk.Button)):
                    child['state'] = state
                _recurse(child)

        _recurse(self.root)

    def _task_wrapper(self, target, stop_event):
        try:
            result = target()
            self.root.after(0, lambda: self._append_log(result if result is not None else '操作完成。'))
        except Exception as exc:
            self.root.after(0, lambda: self._append_log('错误：' + str(exc)))
        finally:
            stop_event.set()
            self.root.after(0, lambda: self._set_status('完成'))
            self.root.after(0, lambda: self._set_progress(100))
            self.root.after(0, lambda: self._disable_buttons(False))

    def _browse_dir(self, var):
        initial = var.get() or '.'
        selected = filedialog.askdirectory(initialdir=initial)
        if selected:
            var.set(selected)

    def _browse_file(self, var):
        initial = var.get() or '.'
        selected = filedialog.asksaveasfilename(initialdir=initial, defaultextension='.xlsx', filetypes=[('Excel 文件', '*.xlsx'), ('所有文件', '*.*')])
        if selected:
            var.set(selected)

    def _save_config(self):
        path_config = self.config.get('path_config', {})
        path_config['download_dir'] = self.download_var.get().strip()
        path_config['classify_dir'] = self.classify_var.get().strip()
        path_config['excel_path'] = self.excel_var.get().strip()
        path_config['copy_target_dir'] = self.copy_var.get().strip()
        path_config['backup_dir'] = self.backup_var.get().strip()

        self.config.config['path_config'] = path_config
        self.config.save_config()
        self.config.ensure_paths()

        new_excel_path = os.path.abspath(path_config['excel_path'])
        if new_excel_path and new_excel_path != os.path.abspath(self.excel.excel_path):
            self.excel.excel_path = new_excel_path
            if not os.path.exists(self.excel.excel_path):
                self.excel.init_excel()
            self.excel.load_workbook()

        self.logger.info('配置已保存。')
        messagebox.showinfo('保存成功', '配置已保存并生效。')
        return '配置已保存。'

    def _init_excel(self):
        self.excel.init_excel()
        self.logger.info('初始化完成：已创建 Excel 文件。')
        self._set_progress(100)
        return '初始化完成。'

    def _scan(self):
        scanner = Scanner(self.config, self.excel, self.logger)
        total, added, updated = scanner.scan_new_movies()
        msg = f'扫描完成：共发现 {total} 个文件，新增 {added} 条，更新 {updated} 条。'
        self.logger.info(msg)
        backup = self.ctx.maybe_backup()
        if backup:
            msg += f' 已备份到 {backup}。'
        self._set_progress(100)
        return msg

    def _actress_lookup(self):
        actress_fetcher = ActressFetcher(self.config, self.logger)
        results, success, failed = actress_fetcher.update_excel_with_actress(self.excel)
        msg_lines = [f'女优查询完成：共处理 {len(results)} 个文件，成功 {success} 个，失败 {failed} 个。']
        for file_path, actress, status in results[:10]:
            if status != 'ok':
                msg_lines.append(f'{os.path.basename(file_path)} -> {status}')
        if len(results) > 10:
            msg_lines.append('... 仅显示前 10 条异常结果。')
        self._set_progress(100)
        return '\n'.join(msg_lines)

    def _classify(self):
        classifier = Classifier(self.config, self.excel, self.logger)
        moved = classifier.classify_all()
        msg = f'分类完成：共移动 {moved} 个文件。'
        self.logger.info(msg)
        backup = self.ctx.maybe_backup()
        if backup:
            msg += f' 已备份到 {backup}。'
        self._set_progress(100)
        return msg

    def _copy(self):
        copier = Copier(self.config, self.excel, self.logger)
        copied = copier.copy_all()
        msg = f'复制完成：共复制 {copied} 个文件。'
        self.logger.info(msg)
        backup = self.ctx.maybe_backup()
        if backup:
            msg += f' 已备份到 {backup}。'
        self._set_progress(100)
        return msg

    def _backup(self):
        backup_target = self.excel.backup_excel(self.config.get('path_config', {}).get('backup_dir'))
        msg = f'备份完成：{backup_target}。'
        self.logger.info(msg)
        self._set_progress(100)
        return msg

    def _fetch(self):
        name = self.fetch_entry.get().strip()
        if not name:
            messagebox.showwarning('提示', '请输入影片名称或代码。')
            return '未执行查询，名称为空。'
        fetcher = MetadataFetcher(self.config, self.logger)
        metadata = fetcher.fetch_metadata(name)
        if metadata:
            lines = [f'{key}: {value}' for key, value in metadata.items()]
            self._set_progress(100)
            return '查询结果：\n' + '\n'.join(lines)
        self._set_progress(100)
        return '未查询到元数据。'

    def _show(self):
        status = self.status_entry.get().strip() or None
        records = self.excel.get_filtered_movies('status', status) if status else self.excel.get_all_movies()
        if not records:
            self._set_progress(100)
            return '当前没有记录。'
        msg = [f'当前记录数：{len(records)}']
        msg.append('第一条记录字段：' + ', '.join(records[0].keys()))
        self._set_progress(100)
        return '\n'.join(msg)

    def run(self):
        self.root.mainloop()
