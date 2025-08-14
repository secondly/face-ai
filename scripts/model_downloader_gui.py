#!/usr/bin/env python3
"""
模型下载器GUI

提供简洁美观的图形界面来下载Deep-Live-Cam所需的模型文件。
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from scripts.download_models import MODELS_CONFIG, download_with_progress, verify_model
    from scripts.check_environment import check_python_version, check_gpu, check_ffmpeg
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)

class ModelDownloaderGUI:
    """模型下载器GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        # self.root.title("Deep-Live-Cam 模型下载器")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 变量
        self.models_dir = tk.StringVar(value=str(PROJECT_ROOT / "models"))
        self.download_thread = None
        self.is_downloading = False
        
        self.setup_ui()
        self.check_environment()
    
    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        # title_label = ttk.Label(main_frame, text="Deep-Live-Cam 模型下载器", 
        #                        font=('Arial', 16, 'bold'))
        # title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 环境状态框架
        env_frame = ttk.LabelFrame(main_frame, text="环境状态", padding="10")
        env_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        env_frame.columnconfigure(1, weight=1)
        
        self.env_status = ttk.Label(env_frame, text="正在检查环境...")
        self.env_status.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # 模型目录选择
        dir_frame = ttk.LabelFrame(main_frame, text="模型保存目录", padding="10")
        dir_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        dir_frame.columnconfigure(1, weight=1)
        
        ttk.Label(dir_frame, text="目录:").grid(row=0, column=0, sticky=tk.W)
        dir_entry = ttk.Entry(dir_frame, textvariable=self.models_dir, width=50)
        dir_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        browse_btn = ttk.Button(dir_frame, text="浏览", command=self.browse_directory)
        browse_btn.grid(row=0, column=2, sticky=tk.W)
        
        # 模型列表框架
        models_frame = ttk.LabelFrame(main_frame, text="可用模型", padding="10")
        models_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        models_frame.columnconfigure(0, weight=1)
        models_frame.rowconfigure(0, weight=1)
        
        # 创建Treeview显示模型列表
        columns = ('name', 'description', 'size', 'status')
        self.models_tree = ttk.Treeview(models_frame, columns=columns, show='headings', height=8)
        
        # 设置列标题
        self.models_tree.heading('name', text='模型名称')
        self.models_tree.heading('description', text='描述')
        self.models_tree.heading('size', text='大小')
        self.models_tree.heading('status', text='状态')
        
        # 设置列宽
        self.models_tree.column('name', width=200)
        self.models_tree.column('description', width=300)
        self.models_tree.column('size', width=80)
        self.models_tree.column('status', width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(models_frame, orient=tk.VERTICAL, command=self.models_tree.yview)
        self.models_tree.configure(yscrollcommand=scrollbar.set)
        
        self.models_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 填充模型列表
        self.populate_models_list()
        
        # 进度框架
        progress_frame = ttk.LabelFrame(main_frame, text="下载进度", padding="10")
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                          maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        self.progress_label = ttk.Label(progress_frame, text="准备就绪")
        self.progress_label.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # 日志框架
        log_frame = ttk.LabelFrame(main_frame, text="下载日志", padding="10")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        # 创建日志文本框和滚动条
        self.log_text = tk.Text(log_frame, height=8, width=80, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 配置网格权重以支持日志区域扩展
        main_frame.rowconfigure(5, weight=1)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=(10, 0))

        # 简化获取按钮 (推荐)
        self.simple_get_btn = ttk.Button(button_frame, text="🚀 简化模型获取",
                                        command=self.simple_model_get)
        self.simple_get_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.download_btn = ttk.Button(button_frame, text="下载选中模型",
                                     command=self.download_selected_models)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.download_all_btn = ttk.Button(button_frame, text="下载所有模型",
                                         command=self.download_all_models)
        self.download_all_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.verify_btn = ttk.Button(button_frame, text="验证模型",
                                   command=self.verify_models)
        self.verify_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.refresh_btn = ttk.Button(button_frame, text="刷新状态",
                                    command=self.refresh_status)
        self.refresh_btn.pack(side=tk.LEFT)
    
    def populate_models_list(self):
        """填充模型列表"""
        for model_name, config in MODELS_CONFIG.items():
            status = self.check_model_status(model_name)
            self.models_tree.insert('', tk.END, values=(
                model_name,
                config['description'],
                f"{config['size_mb']} MB",
                status
            ))
    
    def check_model_status(self, model_name):
        """检查模型状态"""
        model_path = Path(self.models_dir.get()) / model_name
        if not model_path.exists():
            return "未下载"
        
        # 简单的大小检查
        expected_size = MODELS_CONFIG[model_name]['size_mb'] * 1024 * 1024
        actual_size = model_path.stat().st_size
        
        if abs(actual_size - expected_size) / expected_size > 0.1:  # 10%误差
            return "可能损坏"
        
        return "已下载"
    
    def browse_directory(self):
        """浏览目录"""
        directory = filedialog.askdirectory(initialdir=self.models_dir.get())
        if directory:
            self.models_dir.set(directory)
            self.refresh_status()
    
    def check_environment(self):
        """检查环境状态"""
        def check():
            status_parts = []
            
            # 检查Python版本
            if check_python_version():
                status_parts.append("✓ Python")
            else:
                status_parts.append("✗ Python")
            
            # 检查GPU
            if check_gpu():
                status_parts.append("✓ GPU")
            else:
                status_parts.append("⚠ GPU")
            
            # 检查FFmpeg
            if check_ffmpeg():
                status_parts.append("✓ FFmpeg")
            else:
                status_parts.append("✗ FFmpeg")
            
            status_text = " | ".join(status_parts)
            self.env_status.config(text=status_text)
        
        # 在后台线程中检查
        threading.Thread(target=check, daemon=True).start()
    
    def get_selected_models(self):
        """获取选中的模型"""
        selected_items = self.models_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要下载的模型")
            return []
        
        models = []
        for item in selected_items:
            values = self.models_tree.item(item, 'values')
            models.append(values[0])  # 模型名称
        
        return models
    
    def download_selected_models(self):
        """下载选中的模型"""
        models = self.get_selected_models()
        if models:
            self.start_download(models)
    
    def download_all_models(self):
        """下载所有模型"""
        models = list(MODELS_CONFIG.keys())
        self.start_download(models)
    
    def start_download(self, models):
        """开始下载"""
        if self.is_downloading:
            messagebox.showwarning("警告", "正在下载中，请等待完成")
            return

        # 确保目录存在
        models_dir = Path(self.models_dir.get())
        models_dir.mkdir(parents=True, exist_ok=True)

        # 重置进度
        self.progress_var.set(0)
        self.progress_label.config(text="准备开始下载...")

        # 禁用按钮
        self.set_buttons_state(False)
        self.is_downloading = True

        # 在后台线程中下载
        self.download_thread = threading.Thread(
            target=self.download_worker,
            args=(models,),
            daemon=True
        )
        self.download_thread.start()
    
    def download_worker(self, models):
        """下载工作线程"""
        success_count = 0
        total_models = len(models)
        failed_models = []  # 记录失败的模型和原因

        # 清空日志并开始记录
        self.root.after(0, self.clear_log)
        self.root.after(0, lambda: self.log_message(f"开始下载 {total_models} 个模型"))

        try:
            for i, model_name in enumerate(models):
                if model_name not in MODELS_CONFIG:
                    self.root.after(0, lambda mn=model_name: self.log_message(f"跳过未知模型: {mn}", "WARNING"))
                    continue

                config = MODELS_CONFIG[model_name]
                models_dir = Path(self.models_dir.get())
                model_path = models_dir / model_name

                # 更新当前模型信息
                self.root.after(0, lambda mn=model_name, idx=i: self.progress_label.config(
                    text=f"准备下载 {mn} ({idx+1}/{total_models})"
                ))
                self.root.after(0, lambda mn=model_name, idx=i: self.log_message(f"[{idx+1}/{total_models}] 准备下载 {mn}"))

                # 检查文件是否已存在
                if model_path.exists():
                    self.root.after(0, lambda mn=model_name: self.progress_label.config(
                        text=f"{mn} 已存在，跳过"
                    ))
                    self.root.after(0, lambda mn=model_name: self.log_message(f"{mn} 已存在，跳过", "SUCCESS"))
                    success_count += 1
                    # 更新总进度
                    progress = (i + 1) / total_models * 100
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    continue

                # 下载文件
                download_success = False
                last_error = ""

                # 检查是否有可用的下载链接
                if not config['urls']:
                    # 没有直接下载链接，尝试InsightFace下载
                    self.root.after(0, lambda mn=model_name: self.progress_label.config(
                        text=f"{mn}: 没有直接下载链接，尝试InsightFace..."
                    ))
                    self.root.after(0, lambda mn=model_name: self.log_message(f"{mn}: 没有直接下载链接，尝试InsightFace自动下载"))

                    success, error_msg = self.try_insightface_download_gui(model_name, model_path)
                    if success:
                        download_success = True
                        self.root.after(0, lambda mn=model_name: self.log_message(f"{mn}: InsightFace下载成功", "SUCCESS"))
                    else:
                        last_error = f"InsightFace下载失败: {error_msg}"
                        self.root.after(0, lambda mn=model_name, err=error_msg: self.log_message(f"{mn}: InsightFace下载失败 - {err}", "ERROR"))
                else:
                    # 有直接下载链接，逐个尝试
                    for j, url in enumerate(config['urls']):
                        self.root.after(0, lambda idx=j, mn=model_name: self.progress_label.config(
                            text=f"{mn}: 尝试源 {idx+1}/{len(config['urls'])}"
                        ))
                        self.root.after(0, lambda u=url, idx=j, mn=model_name: self.log_message(f"{mn}: 尝试下载源 {idx+1}/{len(config['urls'])}: {u[:50]}..."))

                        success, error_msg = self.download_single_file(url, model_path, model_name)
                        if success:
                            download_success = True
                            self.root.after(0, lambda mn=model_name: self.log_message(f"{mn}: 下载成功", "SUCCESS"))
                            break
                        else:
                            last_error = error_msg
                            self.root.after(0, lambda mn=model_name, err=error_msg: self.log_message(f"{mn}: 下载失败 - {err}", "ERROR"))

                    # 如果直接下载都失败，尝试InsightFace
                    if not download_success:
                        self.root.after(0, lambda mn=model_name: self.log_message(f"{mn}: 直接下载失败，尝试InsightFace..."))
                        success, error_msg = self.try_insightface_download_gui(model_name, model_path)
                        if success:
                            download_success = True
                            self.root.after(0, lambda mn=model_name: self.log_message(f"{mn}: InsightFace下载成功", "SUCCESS"))
                        else:
                            last_error = f"所有方式都失败: {last_error}, InsightFace: {error_msg}"

                if download_success:
                    # 验证文件
                    self.root.after(0, lambda mn=model_name: self.progress_label.config(
                        text=f"{mn}: 验证文件完整性..."
                    ))
                    self.root.after(0, lambda mn=model_name: self.log_message(f"{mn}: 验证文件完整性..."))

                    try:
                        is_valid, msg = verify_model(model_path, config['sha256'])
                        if is_valid:
                            self.root.after(0, lambda mn=model_name: self.progress_label.config(
                                text=f"✓ {mn} 下载并验证完成"
                            ))
                            self.root.after(0, lambda mn=model_name: self.log_message(f"{mn}: 验证通过，下载完成", "SUCCESS"))
                            success_count += 1
                        else:
                            model_path.unlink()  # 删除损坏的文件
                            self.root.after(0, lambda mn=model_name, m=msg: self.progress_label.config(
                                text=f"✗ {mn} 验证失败: {m}"
                            ))
                            self.root.after(0, lambda mn=model_name, m=msg: self.log_message(f"{mn}: 验证失败 - {m}", "ERROR"))
                            failed_models.append(f"{model_name}: 验证失败 - {msg}")
                    except Exception as e:
                        self.root.after(0, lambda mn=model_name, e=e: self.progress_label.config(
                            text=f"✗ {mn} 验证出错: {e}"
                        ))
                        self.root.after(0, lambda mn=model_name, e=e: self.log_message(f"{mn}: 验证出错 - {e}", "ERROR"))
                        failed_models.append(f"{model_name}: 验证出错 - {e}")
                else:
                    if not config['urls']:
                        # 没有直接下载链接的情况
                        self.root.after(0, lambda mn=model_name: self.progress_label.config(
                            text=f"✗ {mn} 需要手动获取"
                        ))
                        self.root.after(0, lambda mn=model_name: self.log_message(f"{mn}: 建议使用InsightFace自动下载", "WARNING"))
                        failed_models.append(f"{model_name}: 建议使用InsightFace自动下载")
                    else:
                        # 有下载链接但都失败的情况
                        self.root.after(0, lambda mn=model_name: self.progress_label.config(
                            text=f"✗ {mn} 所有下载源都失败"
                        ))
                        self.root.after(0, lambda mn=model_name: self.log_message(f"{mn}: 所有下载源都失败", "ERROR"))
                        failed_models.append(f"{model_name}: {last_error}")

                # 更新总进度
                progress = (i + 1) / total_models * 100
                self.root.after(0, lambda p=progress: self.progress_var.set(p))

            # 下载完成，显示结果
            self.root.after(0, lambda: self.log_message(f"下载任务完成: 成功 {success_count}/{total_models}", "SUCCESS" if success_count == total_models else "WARNING"))
            self.root.after(0, lambda: self.download_completed_with_result(success_count, total_models, failed_models))

        except Exception as e:
            self.root.after(0, lambda e=e: self.progress_label.config(
                text=f"下载过程中出错: {e}"
            ))
            self.root.after(0, lambda e=e: self.log_message(f"系统错误: {e}", "ERROR"))
            failed_models.append(f"系统错误: {e}")
            self.root.after(0, lambda: self.download_completed_with_result(success_count, total_models, failed_models))

    def download_single_file(self, url, file_path, model_name):
        """下载单个文件，显示真实进度"""
        # 首先尝试requests
        success, error_msg = self.try_requests_download_gui(url, file_path, model_name)
        if success:
            return True, ""

        # 然后尝试urllib
        success2, error_msg2 = self.try_urllib_download_gui(url, file_path, model_name)
        if success2:
            return True, ""

        # 返回最后一个错误信息
        return False, error_msg2 if error_msg2 else error_msg

    def try_requests_download_gui(self, url, file_path, model_name):
        """GUI版本的requests下载"""
        try:
            import requests

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            self.root.after(0, lambda mn=model_name: self.progress_label.config(
                text=f"{mn}: 使用requests下载..."
            ))

            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(file_path, 'wb') as f:
                downloaded = 0
                last_update = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # 每下载1MB更新一次进度，避免过于频繁的GUI更新
                        if downloaded - last_update > 1024 * 1024 or downloaded == total_size:
                            last_update = downloaded
                            if total_size > 0:
                                percent = min(100, (downloaded * 100) // total_size)
                                # 更新GUI进度
                                self.root.after(0, lambda p=percent, d=downloaded, t=total_size, mn=model_name:
                                    self.progress_label.config(
                                        text=f"{mn}: {p}% ({self.format_size(d)}/{self.format_size(t)})"
                                    )
                                )
                            else:
                                self.root.after(0, lambda d=downloaded, mn=model_name:
                                    self.progress_label.config(
                                        text=f"{mn}: 已下载 {self.format_size(d)}"
                                    )
                                )

            self.root.after(0, lambda mn=model_name: self.progress_label.config(
                text=f"{mn}: 下载完成"
            ))
            return True, ""

        except ImportError:
            error_msg = "requests库未安装"
            self.root.after(0, lambda mn=model_name: self.progress_label.config(
                text=f"{mn}: {error_msg}，尝试urllib..."
            ))
            return False, error_msg
        except Exception as e:
            error_msg = f"requests下载失败: {str(e)}"
            self.root.after(0, lambda e=error_msg, mn=model_name: self.progress_label.config(
                text=f"{mn}: {e}"
            ))
            return False, error_msg

    def try_urllib_download_gui(self, url, file_path, model_name):
        """GUI版本的urllib下载"""
        try:
            import urllib.request
            from urllib.error import URLError

            self.root.after(0, lambda mn=model_name: self.progress_label.config(
                text=f"{mn}: 使用urllib下载..."
            ))

            # 设置User-Agent
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')]
            urllib.request.install_opener(opener)

            last_update = [0]  # 使用列表来在闭包中修改值

            def progress_hook(block_num, block_size, total_size):
                downloaded = block_num * block_size

                # 每下载1MB更新一次进度
                if downloaded - last_update[0] > 1024 * 1024 or (total_size > 0 and downloaded >= total_size):
                    last_update[0] = downloaded
                    if total_size > 0:
                        percent = min(100, (downloaded * 100) // total_size)
                        # 更新GUI进度
                        self.root.after(0, lambda p=percent, d=downloaded, t=total_size, mn=model_name:
                            self.progress_label.config(
                                text=f"{mn}: {p}% ({self.format_size(d)}/{self.format_size(t)})"
                            )
                        )
                    else:
                        self.root.after(0, lambda d=downloaded, mn=model_name:
                            self.progress_label.config(
                                text=f"{mn}: 已下载 {self.format_size(d)}"
                            )
                        )

            urllib.request.urlretrieve(url, file_path, progress_hook)

            self.root.after(0, lambda mn=model_name: self.progress_label.config(
                text=f"{mn}: 下载完成"
            ))
            return True, ""

        except URLError as e:
            error_msg = f"urllib下载失败: {str(e)}"
            self.root.after(0, lambda e=error_msg, mn=model_name: self.progress_label.config(
                text=f"{mn}: {e}"
            ))
            return False, error_msg
        except Exception as e:
            error_msg = f"下载出错: {str(e)}"
            self.root.after(0, lambda e=error_msg, mn=model_name: self.progress_label.config(
                text=f"{mn}: {e}"
            ))
            return False, error_msg

    def try_insightface_download_gui(self, model_name, target_path):
        """GUI版本的InsightFace下载"""
        try:
            import insightface
            import os
            import shutil
            from pathlib import Path

            # 获取InsightFace模型目录
            insightface_root = Path.home() / '.insightface'

            if model_name in MODELS_CONFIG:
                config = MODELS_CONFIG[model_name]
                insightface_name = config.get('insightface_name')

                if insightface_name:
                    # 尝试触发InsightFace自动下载
                    if 'scrfd' in insightface_name or 'arcface' in insightface_name:
                        # 人脸检测和识别模型
                        app = insightface.app.FaceAnalysis(name='buffalo_l')
                        app.prepare(ctx_id=-1, det_size=(640, 640))
                    elif 'inswapper' in insightface_name:
                        # 换脸模型
                        from insightface.model_zoo import get_model
                        swapper = get_model('inswapper_128.onnx', download=True, download_zip=True)

                    # 查找下载的模型文件
                    for root, dirs, files in os.walk(insightface_root):
                        for file in files:
                            if file == model_name or (
                                'scrfd' in model_name and 'det_10g.onnx' in file
                            ) or (
                                'arcface' in model_name and 'rec.onnx' in file
                            ):
                                source_path = Path(root) / file

                                # 复制到目标位置
                                shutil.copy2(source_path, target_path)
                                return True, ""

            return False, "InsightFace中未找到对应模型"

        except ImportError:
            return False, "InsightFace未安装，请运行: pip install insightface"
        except Exception as e:
            return False, str(e)

    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.1f} GB"
    
    def download_completed_with_result(self, success_count, total_count, failed_models=None):
        """下载完成，显示结果"""
        self.is_downloading = False
        self.set_buttons_state(True)

        if failed_models is None:
            failed_models = []

        if success_count == total_count:
            self.progress_label.config(text=f"✓ 所有模型下载完成 ({success_count}/{total_count})")
            messagebox.showinfo("完成", f"模型下载完成！\n成功: {success_count}/{total_count}")
        elif success_count > 0:
            self.progress_label.config(text=f"⚠ 部分模型下载完成 ({success_count}/{total_count})")

            # 显示详细的失败信息
            failed_info = "\n".join(failed_models[:3])  # 最多显示3个失败信息
            if len(failed_models) > 3:
                failed_info += f"\n... 还有 {len(failed_models) - 3} 个失败"

            messagebox.showwarning("部分完成",
                f"部分模型下载完成\n成功: {success_count}/{total_count}\n\n失败详情:\n{failed_info}\n\n建议:\n1. 检查网络连接\n2. 尝试InsightFace自动下载\n3. 手动下载失败的模型")
        else:
            self.progress_label.config(text="✗ 下载失败")

            # 显示详细的失败信息
            failed_info = "\n".join(failed_models[:3])  # 最多显示3个失败信息
            if len(failed_models) > 3:
                failed_info += f"\n... 还有 {len(failed_models) - 3} 个失败"

            messagebox.showerror("失败",
                f"所有模型下载都失败了\n\n失败详情:\n{failed_info}\n\n建议:\n1. 检查网络连接\n2. 尝试InsightFace自动下载\n3. 手动下载模型文件\n4. 查看模型获取指南.md")

        self.refresh_status()

    def download_completed(self):
        """下载完成 (兼容旧版本)"""
        self.download_completed_with_result(0, 1, ["未知错误"])

    def simple_model_get(self):
        """简化模型获取 - 调用简化脚本"""
        if self.is_downloading:
            messagebox.showwarning("警告", "正在下载中，请等待完成")
            return

        # 确认操作
        result = messagebox.askyesno(
            "简化模型获取",
            "这将运行简化模型获取脚本：\n"
            "1. 下载InSwapper模型\n"
            "2. 安装并设置InsightFace\n"
            "3. 下载其他必需模型\n\n"
            "是否继续？"
        )

        if not result:
            return

        # 禁用按钮
        self.set_buttons_state(False)
        self.is_downloading = True

        # 清空日志
        self.clear_log()
        self.log_message("开始简化模型获取")

        # 在后台线程中执行
        import threading
        thread = threading.Thread(target=self.simple_get_worker, daemon=True)
        thread.start()

    def simple_get_worker(self):
        """简化获取的工作线程"""
        try:
            import subprocess
            import sys

            # 运行简化模型获取脚本
            self.root.after(0, lambda: self.log_message("运行简化模型获取脚本..."))

            script_path = Path(__file__).parent / "simple_model_getter.py"

            # 使用Popen来实时获取输出
            process = subprocess.Popen([
                sys.executable, str(script_path)
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
               text=True, bufsize=1, universal_newlines=True)

            # 实时显示输出
            for line in process.stdout:
                line = line.strip()
                if line:
                    # 根据内容判断日志级别
                    if "✅" in line or "成功" in line:
                        level = "SUCCESS"
                    elif "❌" in line or "失败" in line:
                        level = "ERROR"
                    elif "⚠️" in line or "警告" in line:
                        level = "WARNING"
                    else:
                        level = "INFO"

                    self.root.after(0, lambda l=line, lv=level: self.log_message(l, lv))

            # 等待进程完成
            return_code = process.wait()

            if return_code == 0:
                self.root.after(0, lambda: self.log_message("✓ 简化模型获取完成", "SUCCESS"))
                self.root.after(0, lambda: messagebox.showinfo("成功", "模型获取完成！\n请查看日志了解详情。"))
            else:
                self.root.after(0, lambda: self.log_message("✗ 简化模型获取失败", "ERROR"))
                self.root.after(0, lambda: messagebox.showerror("失败", "模型获取失败，请查看日志了解详情。"))

        except Exception as e:
            self.root.after(0, lambda e=e: self.log_message(f"简化获取出错: {e}", "ERROR"))
            self.root.after(0, lambda e=e: messagebox.showerror("错误", f"简化获取出错: {e}"))
        finally:
            # 恢复按钮状态
            self.root.after(0, lambda: self.set_buttons_state(True))
            self.root.after(0, lambda: setattr(self, 'is_downloading', False))
            self.root.after(0, self.refresh_status)
    
    def verify_models(self):
        """验证模型"""
        def verify_worker():
            models_dir = Path(self.models_dir.get())
            results = []
            
            for model_name, config in MODELS_CONFIG.items():
                model_path = models_dir / model_name
                if model_path.exists():
                    is_valid, msg = verify_model(model_path, config['sha256'])
                    results.append(f"{model_name}: {'✓' if is_valid else '✗'} {msg}")
                else:
                    results.append(f"{model_name}: 文件不存在")
            
            result_text = "\n".join(results)
            self.root.after(0, lambda: messagebox.showinfo("验证结果", result_text))
        
        threading.Thread(target=verify_worker, daemon=True).start()
    
    def log_message(self, message, level="INFO"):
        """添加日志消息到日志区域"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # 根据级别设置颜色
        if level == "ERROR":
            color = "red"
        elif level == "WARNING":
            color = "orange"
        elif level == "SUCCESS":
            color = "green"
        else:
            color = "black"

        # 在GUI线程中安全地更新日志
        def update_log():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")

            # 设置颜色标签
            if color != "black":
                start_line = self.log_text.index(tk.END + "-2l linestart")
                end_line = self.log_text.index(tk.END + "-1l lineend")
                tag_name = f"{level}_{timestamp}"
                self.log_text.tag_add(tag_name, start_line, end_line)
                self.log_text.tag_config(tag_name, foreground=color)

            # 自动滚动到底部
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)

        # 如果在主线程中调用，直接更新；否则使用after
        try:
            update_log()
        except:
            self.root.after(0, update_log)

    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def refresh_status(self):
        """刷新状态"""
        # 清空现有项目
        for item in self.models_tree.get_children():
            self.models_tree.delete(item)

        # 重新填充
        self.populate_models_list()
    
    def set_buttons_state(self, enabled):
        """设置按钮状态"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.download_btn.config(state=state)
        self.download_all_btn.config(state=state)
        self.verify_btn.config(state=state)
        self.refresh_btn.config(state=state)
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()

def main():
    """主函数"""
    try:
        app = ModelDownloaderGUI()
        app.run()
    except Exception as e:
        print(f"启动GUI失败: {e}")
        print("请确保已安装tkinter: pip install tk")
        sys.exit(1)

if __name__ == "__main__":
    main()
