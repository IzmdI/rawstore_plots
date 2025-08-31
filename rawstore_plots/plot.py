import matplotlib

matplotlib.use("TkAgg")
import json
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime
import argparse
import logging
from typing import Dict, List, Tuple
import numpy as np
from math import ceil

# Настройка логгера
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Конфигурация графиков
PLOT_CONFIG = {
    "read_iops": {"color": "#1f77b4", "label": "Read IOPS"},
    "write_iops": {"color": "#d62728", "label": "Write IOPS"},
    "read_latency": {"color": "#2ca02c", "label": "Read Latency"},
    "write_latency": {"color": "#ff7f0e", "label": "Write Latency"},
}


class FIOVisualizer:
    def __init__(self):
        self.data: Dict[str, List] = {
            "times": [], "read_iops": [], "read_latency": [],
            "write_iops": [], "write_latency": []
        }
        self.bar_width = 0.6
        self.time_format = "%Y-%m-%d\n%H:%M:%S"

    def calculate_bar_width(self, num_bars: int) -> float:
        """Вычисляет оптимальную ширину столбцов."""
        if num_bars <= 5:
            return 0.35
        elif num_bars <= 15:
            return 0.25
        elif num_bars <= 30:
            return 0.15
        else:
            return max(0.1, 6 / num_bars)

    def load_data(self, file_path: Path) -> bool:
        """Загружает данные из JSONL файла."""
        if not file_path.exists():
            logger.error(f"Файл {file_path} не найден.")
            return False

        try:
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        dt = datetime.fromtimestamp(record["timestamp"])
                        self.data["times"].append(dt)
                        self.data["read_iops"].append(record["read_iops"])
                        self.data["read_latency"].append(record["read_latency_ns"])
                        self.data["write_iops"].append(record["write_iops"])
                        self.data["write_latency"].append(record["write_latency_ns"])
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Пропущена строка: {e}")

            if not self.data["times"]:
                logger.error("Нет данных для построения графиков")
                return False

            return True
        except Exception as e:
            logger.error(f"Ошибка при чтении файла: {e}")
            return False

    def prepare_time_labels(self) -> Tuple[List[str], int]:
        """Подготавливает подписи времени."""
        num_bars = len(self.data["times"])
        self.bar_width = self.calculate_bar_width(num_bars)

        if num_bars > 15:
            self.time_format = "%H:%M:%S"
            if num_bars > 30:
                step = ceil(num_bars / 15)
                time_labels = [
                    dt.strftime(self.time_format) if i % step == 0 else ""
                    for i, dt in enumerate(self.data["times"])
                ]
                return time_labels, num_bars

        time_labels = [dt.strftime(self.time_format) for dt in self.data["times"]]
        return time_labels, num_bars

    def create_grouped_iops_plot(self, output_dir: Path) -> plt.Figure:
        """Создает группированный график IOPS."""
        time_labels, num_bars = self.prepare_time_labels()
        x_pos = np.arange(num_bars)
        bar_width = self.bar_width * 0.8  # Чуть уже для группировки

        fig, ax = plt.subplots(figsize=(max(12, num_bars * 0.6), 7))

        for i, metric in enumerate(["read_iops", "write_iops"]):
            ax.bar(
                x_pos + (i * bar_width) - (bar_width / 2),
                self.data[metric],
                width=bar_width,
                color=PLOT_CONFIG[metric]["color"],
                linewidth=0,
                alpha=0.8,
                label=PLOT_CONFIG[metric]["label"]
            )

        ax.set_title("IOPS Performance (Read/Write)", pad=15, fontsize=14)
        ax.set_xlabel("Measurement Time", labelpad=10)
        ax.set_ylabel("IOPS", labelpad=10)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(time_labels, rotation=45, ha='right', fontsize=9)
        ax.yaxis.grid(True, linestyle=':', alpha=0.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.legend(framealpha=0.9)

        plt.tight_layout()
        output_path = output_dir / "iops_grouped.png"
        plt.savefig(output_path, dpi=120, bbox_inches='tight')
        plt.close()
        logger.info(f"Сохранен группированный график IOPS: {output_path}")
        return fig

    def create_grouped_latency_plot(self, output_dir: Path) -> plt.Figure:
        """Создает группированный график Latency."""
        time_labels, num_bars = self.prepare_time_labels()
        x_pos = np.arange(num_bars)
        bar_width = self.bar_width * 0.8

        fig, ax = plt.subplots(figsize=(max(12, num_bars * 0.6), 7))

        for i, metric in enumerate(["read_latency", "write_latency"]):
            ax.bar(
                x_pos + (i * bar_width) - (bar_width / 2),
                self.data[metric],
                width=bar_width,
                color=PLOT_CONFIG[metric]["color"],
                linewidth=0,
                alpha=0.8,
                label=PLOT_CONFIG[metric]["label"]
            )

        ax.set_title("Latency Performance (Read/Write)", pad=15, fontsize=14)
        ax.set_xlabel("Measurement Time", labelpad=10)
        ax.set_ylabel("Latency (ns)", labelpad=10)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(time_labels, rotation=45, ha='right', fontsize=9)
        ax.yaxis.grid(True, linestyle=':', alpha=0.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.legend(framealpha=0.9)

        plt.tight_layout()
        output_path = output_dir / "latency_grouped.png"
        plt.savefig(output_path, dpi=120, bbox_inches='tight')
        plt.close()
        logger.info(f"Сохранен группированный график Latency: {output_path}")
        return fig

    def create_summary_plot(self, output_dir: Path) -> None:
        """Создает сводный график из группированных данных."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))

        # Настройки для обоих подграфиков
        time_labels, num_bars = self.prepare_time_labels()
        x_pos = np.arange(num_bars)
        bar_width = self.bar_width * 0.7

        # IOPS график (верхний)
        for i, metric in enumerate(["read_iops", "write_iops"]):
            ax1.bar(
                x_pos + (i * bar_width) - (bar_width / 2),
                self.data[metric],
                width=bar_width,
                color=PLOT_CONFIG[metric]["color"],
                linewidth=0,
                alpha=0.8,
                label=PLOT_CONFIG[metric]["label"]
            )

        ax1.set_title("IOPS Performance (Read/Write)", pad=15, fontsize=14)
        ax1.set_ylabel("IOPS", labelpad=10)
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(time_labels, rotation=45, ha='right', fontsize=9)
        ax1.yaxis.grid(True, linestyle=':', alpha=0.5)
        ax1.legend(framealpha=0.9)

        # Latency график (нижний)
        for i, metric in enumerate(["read_latency", "write_latency"]):
            ax2.bar(
                x_pos + (i * bar_width) - (bar_width / 2),
                self.data[metric],
                width=bar_width,
                color=PLOT_CONFIG[metric]["color"],
                linewidth=0,
                alpha=0.8,
                label=PLOT_CONFIG[metric]["label"]
            )

        ax2.set_title("Latency Performance (Read/Write)", pad=15, fontsize=14)
        ax2.set_xlabel("Measurement Time", labelpad=10)
        ax2.set_ylabel("Latency (ns)", labelpad=10)
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(time_labels, rotation=45, ha='right', fontsize=9)
        ax2.yaxis.grid(True, linestyle=':', alpha=0.5)
        ax2.legend(framealpha=0.9)

        # Общие настройки
        fig.suptitle(
            f"FIO Performance Summary ({num_bars} measurements)",
            y=1.02,
            fontsize=16,
            fontweight='bold'
        )

        plt.tight_layout()
        output_path = output_dir / "fio_summary.png"
        plt.savefig(output_path, dpi=120, bbox_inches='tight')
        plt.close()
        logger.info(f"Сохранен сводный график: {output_path}")

    def visualize(self, file_path: Path, output_dir: Path) -> None:
        """Основной метод для визуализации данных."""
        output_dir.mkdir(parents=True, exist_ok=True)

        if not self.load_data(file_path):
            return

        # Создаем группированные графики
        self.create_grouped_iops_plot(output_dir)
        self.create_grouped_latency_plot(output_dir)

        # Создаем сводный график
        self.create_summary_plot(output_dir)


def main():
    parser = argparse.ArgumentParser(
        description='FIO Test Results Visualizer - Bar Charts',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # parser.add_argument(
    #     'input',
    #     type=Path,
    #     help='Path to input JSONL file with FIO results'
    # )
    parser.add_argument(
        '-i',
        '--input',
        type=Path,
        default=Path("../assets/fio_summary.jsonl"),
        help='Path to input JSONL file with FIO results'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path("../bar_plots"),
        help='Output directory for bar plots'
    )
    parser.add_argument(
        '--dpi',
        type=int,
        default=120,
        help='DPI for output images'
    )

    args = parser.parse_args()

    visualizer = FIOVisualizer()
    visualizer.visualize(args.input, args.output)


if __name__ == "__main__":
    main()
