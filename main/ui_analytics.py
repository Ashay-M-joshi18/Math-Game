import csv
import math
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from models import get_detailed_analytics, reset_student_analytics

FONT_FAMILY_UI = "Segoe UI"
PERFORMANCE_GROWTH_BASE = math.log((math.pi ** 2) - 5)
PAGE_BG = "#f4f7fb"
SURFACE_BG = "#ffffff"
SURFACE_ALT_BG = "#eef4fb"
ACCENT_BLUE = "#1f5aa6"
ACCENT_TEAL = "#1e8f8f"
TEXT_PRIMARY = "#1f2a37"
TEXT_SECONDARY = "#5b6777"
OUTLINE = "#d8e2ef"


class DetailedAnalyticsWindow(tk.Toplevel):
    def __init__(
        self,
        parent,
        student_data,
        analytics_list,
        allow_reset=False,
        allow_export=False,
        on_reset=None,
        viewer_mode="admin",
    ):
        super().__init__(parent)
        self.student_data = student_data
        self.analytics_list = analytics_list or []
        self.allow_reset = allow_reset
        self.allow_export = allow_export
        self.on_reset = on_reset
        self.viewer_mode = viewer_mode
        self.basic_topics = ["Addition", "Subtraction", "Multiplication", "Division", "Mixed"]
        self.adv_topics = ["Squares", "Cubes", "Square Root", "Cube Root", "Advanced Quiz"]
        self.t20_topics = ["Addition", "Subtraction", "Multiplication", "Division"]
        self.all_topics = self.basic_topics + self.adv_topics + self.t20_topics

        profile_heading = "My Progress" if self.viewer_mode == "student" else "Mastery Profile"
        profile_summary = (
            "Track your scores, speed, and flex points across basic, advanced, and T20 maths"
            if self.viewer_mode == "student"
            else "Progress overview across basic, advanced, and T20 maths"
        )

        self.title(f"{profile_heading}: {student_data['name']}")
        self.geometry("1040x730")
        self.minsize(980, 680)
        self.configure(bg=PAGE_BG)

        self._configure_styles()

        header = tk.Frame(self, bg=PAGE_BG, padx=24, pady=24)
        header.pack(fill="x")

        title_row = tk.Frame(header, bg=PAGE_BG)
        title_row.pack(fill="x")

        identity_frame = tk.Frame(title_row, bg=PAGE_BG)
        identity_frame.pack(side="left", fill="x", expand=True)

        tk.Label(
            identity_frame,
            text=profile_heading,
            fg=ACCENT_BLUE,
            bg=PAGE_BG,
            font=(FONT_FAMILY_UI, 11, "bold"),
        ).pack(anchor="w")

        tk.Label(
            identity_frame,
            text=student_data["name"],
            fg=TEXT_PRIMARY,
            bg=PAGE_BG,
            font=(FONT_FAMILY_UI, 22, "bold"),
        ).pack(anchor="w", pady=(2, 0))

        meta_parts = []
        login_id = student_data.get("login_id")
        if login_id and login_id != "N/A":
            meta_parts.append(f"Login ID: {login_id}")
        meta_parts.append(profile_summary)
        tk.Label(
            identity_frame,
            text="  |  ".join(meta_parts),
            fg=TEXT_SECONDARY,
            bg=PAGE_BG,
            font=(FONT_FAMILY_UI, 10),
        ).pack(anchor="w", pady=(6, 0))

        attempt_count = len(self.analytics_list)
        badge = tk.Frame(
            title_row,
            bg="#dfefff",
            highlightbackground="#b8d3f0",
            highlightthickness=1,
            padx=18,
            pady=12,
        )
        badge.pack(side="right")
        tk.Label(
            badge,
            text=str(attempt_count),
            fg=ACCENT_BLUE,
            bg="#dfefff",
            font=(FONT_FAMILY_UI, 20, "bold"),
        ).pack(anchor="center")
        tk.Label(
            badge,
            text="Attempts",
            fg=TEXT_PRIMARY,
            bg="#dfefff",
            font=(FONT_FAMILY_UI, 10, "bold"),
        ).pack(anchor="center", pady=(2, 0))

        self._build_summary_strip(header)

        action_bar = tk.Frame(self, bg=SURFACE_BG, pady=12, padx=16, highlightbackground=OUTLINE, highlightthickness=1)
        action_bar.pack(fill="x", padx=24, pady=(0, 12))

        if self.allow_export:
            tk.Button(
                action_bar,
                text="Download CSV",
                command=self._export_csv,
                font=(FONT_FAMILY_UI, 10, "bold"),
                bg="#2F6FB4",
                fg="white",
                activebackground="#285F99",
                activeforeground="white",
                relief="raised",
                bd=1,
                padx=12,
                pady=6,
                cursor="hand2",
                highlightthickness=0,
            ).pack(side="left")

        if self.allow_reset:
            tk.Button(
                action_bar,
                text="Reset Student Data",
                command=self._reset_student_analytics,
                font=(FONT_FAMILY_UI, 10, "bold"),
                bg="#C0392B",
                fg="white",
                activebackground="#A93226",
                activeforeground="white",
                relief="raised",
                bd=1,
                padx=12,
                pady=6,
                cursor="hand2",
                highlightthickness=0,
            ).pack(side="left", padx=(10, 0))

            self._build_performance_legend(action_bar)
        elif not self.allow_export:
            tk.Label(
                action_bar,
                text="Use this dashboard to review your progress, compare topics, and build more flex points.",
                bg=SURFACE_BG,
                fg=TEXT_SECONDARY,
                font=(FONT_FAMILY_UI, 10),
            ).pack(side="left")

        notebook_shell = tk.Frame(self, bg=SURFACE_BG, highlightbackground=OUTLINE, highlightthickness=1)
        notebook_shell.pack(expand=True, fill="both", padx=24, pady=(0, 24))

        self.tabs = ttk.Notebook(notebook_shell, style="Profile.TNotebook")
        self.tabs.pack(expand=True, fill="both", padx=16, pady=16)

        self.tab_basic = tk.Frame(self.tabs, bg=PAGE_BG)
        self.tab_advanced = tk.Frame(self.tabs, bg=PAGE_BG)
        self.tab_t20 = tk.Frame(self.tabs, bg=PAGE_BG)

        self.tabs.add(self.tab_basic, text="Basic Operations")
        self.tabs.add(self.tab_advanced, text="Advanced Maths")
        self.tabs.add(self.tab_t20, text="T20")

        self.tab_basic_content = self._create_scrollable_tab_content(self.tab_basic)
        self.tab_advanced_content = self._create_scrollable_tab_content(self.tab_advanced)
        self.tab_t20_content = self._create_scrollable_tab_content(self.tab_t20)

        self._render_analytics()

    def _create_scrollable_tab_content(self, parent):
        canvas = tk.Canvas(parent, bg=PAGE_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas, bg=PAGE_BG)
        content_window = canvas.create_window((0, 0), window=content, anchor="nw")

        content.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(content_window, width=event.width),
        )

        canvas.bind("<Enter>", lambda _event, target=canvas: self._bind_mousewheel(target))
        canvas.bind("<Leave>", lambda _event: self._unbind_mousewheel())

        return content

    def _bind_mousewheel(self, canvas):
        canvas.bind_all("<MouseWheel>", lambda event, target=canvas: target.yview_scroll(int(-event.delta / 120), "units"))

    def _unbind_mousewheel(self):
        self.unbind_all("<MouseWheel>")

    def _configure_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Profile.TNotebook", background=SURFACE_BG, borderwidth=0)
        style.configure(
            "Profile.TNotebook.Tab",
            padding=(18, 10),
            font=(FONT_FAMILY_UI, 10, "bold"),
            background="#dfe8f5",
            foreground=TEXT_SECONDARY,
            borderwidth=0,
        )
        style.map(
            "Profile.TNotebook.Tab",
            background=[("selected", SURFACE_BG), ("active", "#e8f0fb")],
            foreground=[("selected", ACCENT_BLUE), ("active", TEXT_PRIMARY)],
        )

    def _build_summary_strip(self, parent):
        metrics = self._calculate_summary_metrics()
        summary_row = tk.Frame(parent, bg=PAGE_BG)
        summary_row.pack(fill="x", pady=(18, 0))

        cards = [
            ("Progress", metrics["progress"], metrics["progress_hint"]),
            ("Average Accuracy", metrics["avg_accuracy"], "Across recorded attempts"),
            ("Flex Points", metrics["total_flex_points"], "Built from score, speed, and level"),
            ("Strongest Area", metrics["best_topic"], metrics["best_band"]),
        ]

        for index, (label, value, hint) in enumerate(cards):
            card = tk.Frame(
                summary_row,
                bg=SURFACE_BG,
                padx=16,
                pady=14,
                highlightbackground=OUTLINE,
                highlightthickness=1,
            )
            card.grid(row=0, column=index, padx=(0, 12 if index < len(cards) - 1 else 0), sticky="nsew")

            tk.Label(
                card,
                text=label,
                bg=SURFACE_BG,
                fg=TEXT_SECONDARY,
                font=(FONT_FAMILY_UI, 9, "bold"),
            ).pack(anchor="w")
            tk.Label(
                card,
                text=value,
                bg=SURFACE_BG,
                fg=TEXT_PRIMARY,
                font=(FONT_FAMILY_UI, 16, "bold"),
            ).pack(anchor="w", pady=(8, 4))
            tk.Label(
                card,
                text=hint,
                bg=SURFACE_BG,
                fg=TEXT_SECONDARY,
                font=(FONT_FAMILY_UI, 9),
            ).pack(anchor="w")

        for index in range(len(cards)):
            summary_row.grid_columnconfigure(index, weight=1)

    def _calculate_summary_metrics(self):
        valid_entries = [entry for entry in self.analytics_list if entry.get("topic")]
        total_topics = len(self.basic_topics) + len(self.adv_topics) + len(self.t20_topics)
        if not valid_entries:
            return {
                "progress": f"0/{total_topics}",
                "progress_hint": "0% of available topics",
                "avg_accuracy": "0%",
                "total_flex_points": "0.00",
                "best_topic": "No Data",
                "best_band": "Awaiting attempts",
            }

        covered_topics = set()
        for entry in valid_entries:
            topic = entry.get("topic")
            section = entry.get("section")
            if section == "Basic" and topic in self.basic_topics:
                covered_topics.add((section, topic))
            elif section == "Advanced" and topic in self.adv_topics:
                covered_topics.add((section, topic))
            elif section == "T20" and topic in self.t20_topics:
                covered_topics.add((section, topic))

        topics_covered = len(covered_topics)
        progress_pct = round((topics_covered / total_topics) * 100) if total_topics else 0
        avg_accuracy = sum(float(entry.get("accuracy", 0.0)) for entry in valid_entries) / len(valid_entries)
        total_flex_points = self._calculate_flex_points(valid_entries)

        best_entry = None
        best_score = -1.0
        for entry in valid_entries:
            difficulty = self._get_scaled_difficulty(entry)
            score, band, _ = self._calculate_performance_band(
                entry.get("accuracy", 0.0),
                entry.get("time_per_q", 0.0),
                difficulty,
            )
            if score > best_score:
                best_score = score
                best_entry = (entry.get("topic", "No Data"), band)

        return {
            "progress": f"{topics_covered}/{total_topics}",
            "progress_hint": f"{progress_pct}% of available topics",
            "avg_accuracy": f"{round(avg_accuracy * 100)}%",
            "total_flex_points": f"{total_flex_points:.2f}",
            "best_topic": best_entry[0] if best_entry else "No Data",
            "best_band": best_entry[1] if best_entry else "Awaiting attempts",
        }

    def _get_scaled_difficulty(self, entry):
        topic = entry.get("topic")
        section = entry.get("section")
        try:
            logical_level = 4 if topic in ("Advanced Quiz", "Advance Maths Quiz") else int(entry.get("sub_level", 1) or 1)
        except (TypeError, ValueError):
            logical_level = 1

        # T20 stores two explicit modes (easy/hard); preserve those as 1/2 directly.
        if section == "T20":
            return max(1, logical_level)

        if topic in ["Addition", "Subtraction", "Mixed"]:
            return ((logical_level - 1) // 2) + 1
        return max(1, logical_level)

    def _calculate_flex_points(self, entries):
        flex_point_sum = 0.0
        for entry in entries:
            score = float(entry.get("score", 0) or 0)
            accuracy_factor = max(0.0, float(entry.get("accuracy", 0) or 0))
            time_penalty = 1.0 + max(0.0, float(entry.get("time_per_q", 0) or 0))
            if time_penalty <= 0:
                continue
            flex_point_sum += (score * accuracy_factor * self._get_scaled_difficulty(entry)) / time_penalty
        return round(flex_point_sum, 2)

    def _build_performance_legend(self, parent):
        legend_frame = tk.Frame(parent, bg=SURFACE_BG)
        legend_frame.pack(side="right")

        tk.Label(
            legend_frame,
            text="Remark:",
            bg=SURFACE_BG,
            fg=TEXT_PRIMARY,
            font=(FONT_FAMILY_UI, 10, "bold"),
        ).pack(side="left", padx=(0, 8))

        for color_hex, label_text in (
            ("#e74c3c", "Needs Practice"),
            ("#f1c40f", "Developing"),
            ("#2ecc71", "Strong"),
            ("#2e5dcc", "Mastery"),
        ):
            item_frame = tk.Frame(legend_frame, bg=SURFACE_BG)
            item_frame.pack(side="left", padx=(0, 10))

            tk.Label(
                item_frame,
                text="  ",
                bg=color_hex,
                relief="solid",
                bd=1,
            ).pack(side="left", padx=(0, 4))
            tk.Label(
                item_frame,
                text=label_text,
                bg=SURFACE_BG,
                fg=TEXT_PRIMARY,
                font=(FONT_FAMILY_UI, 9),
            ).pack(side="left")

    def _render_analytics(self):
        for tab in (self.tab_basic_content, self.tab_advanced_content, self.tab_t20_content):
            for widget in tab.winfo_children():
                widget.destroy()

        self._populate_mastery_table(self.tab_basic_content, "Basic", self.basic_topics)
        self._populate_mastery_table(self.tab_advanced_content, "Advanced", self.adv_topics)
        self._populate_mastery_table(self.tab_t20_content, "T20", self.t20_topics)

    def _build_topic_rows(self, section, topics):
        section_data = [entry for entry in self.analytics_list if entry.get("section") == section]
        rows = []

        for topic in topics:
            topic_attempts = [entry for entry in section_data if entry.get("topic") == topic]

            if topic_attempts:
                count = len(topic_attempts)
                scores = [entry.get("score", 0) for entry in topic_attempts]
                accuracies = [entry.get("accuracy", 0) for entry in topic_attempts]
                times = [entry.get("time_per_q", 1) for entry in topic_attempts]

                best_score = max(scores)
                avg_score = round(sum(scores) / count, 2)
                avg_accuracy = round(sum(accuracies) / count, 2)
                avg_time = round(sum(times) / count, 2)

                scaled_levels = [self._get_scaled_difficulty(entry) for entry in topic_attempts]
                avg_difficulty = round(sum(scaled_levels) / count, 2)
                flex_points = self._calculate_flex_points(topic_attempts)
                performance_score, performance_band, performance_color = self._calculate_performance_band(
                    avg_accuracy,
                    avg_time,
                    avg_difficulty,
                )
            else:
                count = 0
                best_score = "-"
                avg_score = "-"
                avg_accuracy = "-"
                avg_time = "-"
                avg_difficulty = "-"
                flex_points = "-"
                performance_score = "-"
                performance_band = "No Data"
                performance_color = "#ecf0f1"

            rows.append(
                {
                    "Topic": topic,
                    "Best Score": best_score,
                    "Avg Score": avg_score,
                    "Avg Accuracy": avg_accuracy,
                    "Avg Time/Q": avg_time,
                    "Avg Difficulty": avg_difficulty,
                    "Attempts": count,
                    "Flex Points": flex_points,
                    "Performance Score": performance_score,
                    "Performance Band": performance_band,
                    "Row Color": performance_color,
                }
            )

        return rows

    def _calculate_performance_band(self, avg_accuracy, avg_time_per_question, avg_difficulty_level):
        safe_accuracy = max(0.0, float(avg_accuracy or 0.0))
        safe_time = max(0.01, float(avg_time_per_question or 0.0))
        safe_difficulty = max(0.0, float(avg_difficulty_level or 0.0))

        performance_score = safe_accuracy * (1.0 / safe_time**0.5) * (PERFORMANCE_GROWTH_BASE ** safe_difficulty)
        performance_score = round(performance_score, 4)

        if performance_score < 0.40:
            return performance_score, "Needs Practice", "#e74c3c"
        elif performance_score < 0.70:
            return performance_score, "Developing", "#f1c40f"
        elif performance_score < 1.20:
            return performance_score, "Strong", "#2ecc71"
        return performance_score, "Mastery", "#2e5dcc"

    def _populate_mastery_table(self, parent, section, topics):
        table_frame = tk.Frame(parent, bg=PAGE_BG)
        table_frame.pack(fill="x", padx=20, pady=(15, 5))

        cols = (
            "Topic",
            "Best Score",
            "Avg Score",
            "Avg Accuracy",
            "Avg Time/Q",
            "Avg Difficulty",
            "Attempts",
            "Flex Points",
            "Performance",
            "Band",
        )
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=6)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=125, anchor="center")
        tree.column("Topic", width=150, anchor="w")
        tree.column("Band", width=110, anchor="center")
        tree.tag_configure("perf_low", background="#e74c3c", foreground="white")
        tree.tag_configure("perf_mid", background="#f1c40f", foreground="black")
        tree.tag_configure("perf_high", background="#2ecc71", foreground="white")
        tree.tag_configure("perf_higher", background="#2e5dcc", foreground="white")
        tree.tag_configure("perf_none", background="#ecf0f1", foreground="black")
        tree.pack(fill="x")

        chart_frame = tk.Frame(parent, bg="white")
        chart_frame.pack(fill="both", expand=True, padx=20, pady=(5, 15))

        topic_rows = self._build_topic_rows(section, topics)
        chart_labels = []
        chart_avg_scores = []
        chart_best_scores = []

        for row in topic_rows:
            if row["Performance Band"] == "Needs Practice":
                row_tag = "perf_low"
            elif row["Performance Band"] == "Developing":
                row_tag = "perf_mid"
            elif row["Performance Band"] == "Strong":
                row_tag = "perf_high"
            elif row["Performance Band"] == "Mastery":
                row_tag = "perf_higher"
            else:
                row_tag = "perf_none"

            tree.insert(
                "",
                "end",
                values=(
                    row["Topic"],
                    row["Best Score"],
                    row["Avg Score"],
                    row["Avg Accuracy"],
                    row["Avg Time/Q"],
                    row["Avg Difficulty"],
                    row["Attempts"],
                    row["Flex Points"],
                    row["Performance Score"],
                    row["Performance Band"],
                ),
                tags=(row_tag,),
            )
            chart_labels.append(row["Topic"])
            chart_avg_scores.append(row["Avg Score"] if row["Avg Score"] != "-" else 0)
            chart_best_scores.append(row["Best Score"] if row["Best Score"] != "-" else 0)

        fig, ax = plt.subplots(figsize=(8, 2.8))
        fig.patch.set_facecolor("#f9f9f9")
        ax.set_facecolor("#f9f9f9")

        x = range(len(chart_labels))
        width = 0.35
        bars1 = ax.bar([i - width / 2 for i in x], chart_avg_scores, width, label="Avg Score", color="#4CAF50", alpha=0.85)
        bars2 = ax.bar([i + width / 2 for i in x], chart_best_scores, width, label="Best Score", color="#2196F3", alpha=0.85)

        ax.set_xticks(list(x))
        ax.set_xticklabels(chart_labels, fontsize=9)
        ax.set_ylabel("Score", fontsize=9)
        # ax.set_title(f"{section} — Score by Topic", fontsize=10, fontweight="bold")
        ax.legend(fontsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        for bar in bars1:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, height + 0.3, str(round(height, 1)), ha="center", va="bottom", fontsize=7)
        for bar in bars2:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, height + 0.3, str(round(height, 1)), ha="center", va="bottom", fontsize=7)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)

    def _export_csv(self):
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", self.student_data.get("name", "student")).strip("_") or "student"
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Analytics CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"{safe_name}_analytics.csv",
        )
        if not file_path:
            return

        try:
            headers = [
                "Section",
                "Topic",
                "Best Score",
                "Avg Score",
                "Avg Accuracy",
                "Avg Time/Q",
                "Avg Difficulty",
                "Attempts",
                "Flex Points",
                "Performance Score",
                "Performance Band",
            ]
            with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(headers)

                for section_label, section_key, topics in (
                    ("Basic Operations", "Basic", self.basic_topics),
                    ("Advanced Maths", "Advanced", self.adv_topics),
                    ("T20", "T20", self.t20_topics),
                ):
                    for row in self._build_topic_rows(section_key, topics):
                        writer.writerow([
                            section_label,
                            row["Topic"],
                            row["Best Score"],
                            row["Avg Score"],
                            row["Avg Accuracy"],
                            row["Avg Time/Q"],
                            row["Avg Difficulty"],
                            row["Attempts"],
                            row["Flex Points"],
                            row["Performance Score"],
                            row["Performance Band"],
                        ])

            messagebox.showinfo("Export Success", f"CSV exported to:\n{file_path}", parent=self)
        except Exception as exc:
            messagebox.showerror("Export Error", f"Could not export CSV.\n{exc}", parent=self)

    def _reset_student_analytics(self):
        student_name = self.student_data.get("name", "this student")
        student_id = self.student_data.get("id")
        if not student_id:
            messagebox.showerror("Reset Error", "Student record is missing an ID.", parent=self)
            return

        confirmed = messagebox.askyesno(
            "Reset Analytics",
            f"Delete all analytics attempts for {student_name}?\n\nThis cannot be undone.",
            parent=self,
        )
        if not confirmed:
            return

        try:
            deleted_rows = reset_student_analytics(student_id)
        except Exception as exc:
            messagebox.showerror("Reset Error", f"Could not reset analytics.\n{exc}", parent=self)
            return

        if deleted_rows is None:
            messagebox.showerror("Reset Error", "Student record was not found.", parent=self)
            return

        self.analytics_list = get_detailed_analytics(student_id)
        self._render_analytics()
        if callable(self.on_reset):
            self.on_reset()

        if deleted_rows == 0:
            messagebox.showinfo("Reset Complete", f"No analytics attempts were found for {student_name}.", parent=self)
        else:
            messagebox.showinfo(
                "Reset Complete",
                f"Deleted {deleted_rows} analytics attempt(s) for {student_name}.",
                parent=self,
            )
