import json
from pathlib import Path


def _read_last_line(path: Path) -> str:
    with path.open("rb") as f:
        f.seek(0, 2)
        pos = f.tell()
        if pos == 0:
            return ""
        line = b""
        while pos > 0:
            pos -= 1
            f.seek(pos)
            char = f.read(1)
            if char == b"\n" and line:
                break
            line = char + line
        return line.decode("utf-8").strip()


def merge_fio_results(
    input_path: Path, output_file: str = "fio_summary"
) -> None:
    """
    Parse fio results from json's and collects it into summary jsonl file.
    Each run appends only the newest records to the end of the file.
    :param input_path: Input directory where fio's results are stored.
    :param output_file: Name of output file with merged results.
    :return: None
    """
    output_path = input_path / Path(output_file + ".jsonl")
    last_timestamp = -1
    if output_path.exists() and output_path.stat().st_size > 0:
        last_line = _read_last_line(output_path)
        last_record = json.loads(last_line)
        last_timestamp = last_record.get("timestamp", -1)

    file_list = input_path.glob("*.json")
    data = list()
    for file_path in file_list:
        with open(file_path, "r") as input_file:
            fio = json.load(input_file)
        timestamp = fio["timestamp"]
        if timestamp <= last_timestamp:
            continue

        job = fio["jobs"][0]
        data.append(
            {
                "timestamp": fio["timestamp"],
                "time": fio["time"],
                "commit": file_path.name.replace(".json", ""),
                "read_iops": job["read"]["iops_mean"],
                "read_latency_ns": job["read"]["lat_ns"]["mean"],
                "write_iops": job["write"]["iops_mean"],
                "write_latency_ns": job["write"]["lat_ns"]["mean"],
            }
        )
    if data:
        data.sort(key=lambda x: x["timestamp"])
        with open(output_path, "a", encoding="utf-8") as out:
            for record in data:
                out.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    data_dir = Path("../data")
    merge_fio_results(data_dir)
