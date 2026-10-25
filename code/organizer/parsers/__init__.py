"""Pick a parser by file extension."""

from pathlib import Path

from organizer.parsers.common import ParsedFile
from organizer.parsers.extracted_parser import parse_extracted
from organizer.parsers.json_parser import parse_json
from organizer.parsers.log_parser import parse_log
from organizer.parsers.sql_parser import parse_sql
from organizer.parsers.text_parser import parse_text

PARSERS = {
    ".sql": parse_sql,
    ".json": parse_json,
    ".log": parse_log,
    ".txt": parse_text,
    ".png": parse_extracted,
    ".pdf": parse_extracted,
}


def parse_file(path: Path) -> ParsedFile:
    parser = PARSERS.get(path.suffix.lower())
    return parser(path) if parser else ParsedFile(meta={"unsupported": path.suffix})
