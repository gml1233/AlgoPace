#!/usr/bin/env python3
"""
历史记录存储模块：SQLite + 文件目录。
提供 save_record, list_records, get_record, delete_record, export_record。
"""
import json
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 数据目录：项目根目录下的 data/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = _PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "algo_history.db"
HISTORY_FILES_DIR = DATA_DIR / "history"

RECORD_TYPE_GENERATE = "generate"
RECORD_TYPE_RERENDER = "rerender"


def _ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_FILES_DIR.mkdir(parents=True, exist_ok=True)


def _get_conn() -> sqlite3.Connection:
    _ensure_dirs()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表结构。"""
    _ensure_dirs()
    conn = _get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept TEXT NOT NULL,
                language TEXT NOT NULL,
                voice_name TEXT,
                knowledge_file_path TEXT,
                manim_code TEXT NOT NULL,
                srt_content TEXT NOT NULL,
                subtitle_font TEXT,
                subtitle_font_size REAL,
                subtitle_font_color TEXT,
                subtitle_auto_wrap INTEGER,
                subtitle_alignment TEXT,
                saved_at TEXT NOT NULL,
                record_type TEXT NOT NULL,
                agent_params TEXT,
                scene_durations TEXT,
                conversation_history TEXT
            )
        """)
        conn.commit()
        # 迁移：若表已存在且无 agent_params 列，则添加
        try:
            conn.execute("ALTER TABLE history ADD COLUMN agent_params TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # 列已存在
        # 迁移：若表已存在且无 scene_durations 列，则添加
        try:
            conn.execute("ALTER TABLE history ADD COLUMN scene_durations TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # 列已存在
        # 迁移：若表已存在且无 conversation_history 列，则添加
        try:
            conn.execute("ALTER TABLE history ADD COLUMN conversation_history TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # 列已存在
    finally:
        conn.close()


def save_record(
    concept: str,
    language: str,
    voice_name: Optional[str],
    knowledge_file_path: Optional[str],
    manim_code: str,
    srt_content: str,
    subtitle_font: Optional[str] = None,
    subtitle_font_size: Optional[float] = None,
    subtitle_font_color: Optional[str] = None,
    subtitle_auto_wrap: bool = True,
    subtitle_alignment: Optional[str] = None,
    record_type: str = RECORD_TYPE_GENERATE,
    agent_params: Optional[Dict[str, Any]] = None,
    scene_durations: Optional[Dict[str, float]] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> int:
    """
    保存一条历史记录。若有知识文档则复制到 data/history/{id}/ 并记路径。
    agent_params 为各 Agent 的请求参数字典（JSON 序列化存储）。
    scene_durations 为视频场景时长字典 (scene_id -> seconds)。
    conversation_history 为对话历史消息列表。
    返回新记录的 id。
    """
    init_db()
    saved_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    # 注意：这里不要用 truthiness 判断。
    # - 空 dict / 空 list 也属于“有效状态”，应当落库为 "{}" 或 "[]"
    # - 否则会被写成 NULL，导致导入时无法恢复状态
    agent_params_json = (
        json.dumps(agent_params, ensure_ascii=False) if agent_params is not None else None
    )
    scene_durations_json = (
        json.dumps(scene_durations, ensure_ascii=False) if scene_durations is not None else None
    )
    conversation_history_json = (
        json.dumps(conversation_history, ensure_ascii=False) if conversation_history is not None else None
    )
    conn = _get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO history (
                concept, language, voice_name, knowledge_file_path,
                manim_code, srt_content,
                subtitle_font, subtitle_font_size, subtitle_font_color,
                subtitle_auto_wrap, subtitle_alignment, saved_at, record_type,
                agent_params, scene_durations, conversation_history
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                concept or "",
                language or "English",
                voice_name or "",
                "",  # 先空，插入后得到 id 再复制文件并更新
                manim_code or "",
                srt_content or "",
                subtitle_font or "Arial",
                float(subtitle_font_size) if subtitle_font_size is not None else 24.0,
                subtitle_font_color or "#FFFFFF",
                1 if subtitle_auto_wrap else 0,
                subtitle_alignment or "居中对齐",
                saved_at,
                record_type or RECORD_TYPE_GENERATE,
                agent_params_json,
                scene_durations_json,
                conversation_history_json,
            ),
        )
        record_id = cur.lastrowid
        conn.commit()

        # 若有知识文档，复制到 data/history/{record_id}/
        stored_path = ""
        if knowledge_file_path and os.path.isfile(knowledge_file_path):
            record_dir = HISTORY_FILES_DIR / str(record_id)
            record_dir.mkdir(parents=True, exist_ok=True)
            ext = Path(knowledge_file_path).suffix or ".txt"
            dest = record_dir / f"knowledge{ext}"
            shutil.copy2(knowledge_file_path, dest)
            stored_path = str(dest.relative_to(DATA_DIR))
            conn.execute(
                "UPDATE history SET knowledge_file_path = ? WHERE id = ?",
                (stored_path, record_id),
            )
            conn.commit()
        return record_id
    finally:
        conn.close()


def list_records(
    limit: int = 50,
    offset: int = 0,
    record_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """返回历史记录列表，每项含 id, concept, saved_at, record_type 等摘要。"""
    init_db()
    conn = _get_conn()
    try:
        if record_type:
            rows = conn.execute(
                """
                SELECT id, concept, saved_at, record_type
                FROM history
                WHERE record_type = ?
                ORDER BY saved_at DESC
                LIMIT ? OFFSET ?
                """,
                (record_type, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, concept, saved_at, record_type
                FROM history
                ORDER BY saved_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_record(record_id: int) -> Optional[Dict[str, Any]]:
    """返回单条完整记录，knowledge 字段为绝对路径（若存在）。"""
    init_db()
    conn = _get_conn()
    try:
        row = conn.execute("SELECT * FROM history WHERE id = ?", (record_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        # 将 knowledge_file_path 转为绝对路径
        rel = d.get("knowledge_file_path") or ""
        if rel:
            abs_path = DATA_DIR / rel
            if abs_path.exists():
                d["knowledge_file_path"] = str(abs_path)
            else:
                d["knowledge_file_path"] = None
        else:
            d["knowledge_file_path"] = None
        d["subtitle_auto_wrap"] = bool(d.get("subtitle_auto_wrap", 1))
        raw = d.get("agent_params")
        if raw:
            try:
                d["agent_params"] = json.loads(raw)
            except (TypeError, ValueError):
                d["agent_params"] = {}
        else:
            d["agent_params"] = {}
        # 解析 scene_durations
        sd_raw = d.get("scene_durations")
        if sd_raw:
            try:
                d["scene_durations"] = json.loads(sd_raw)
            except (TypeError, ValueError):
                d["scene_durations"] = None
        else:
            d["scene_durations"] = None
        # 解析 conversation_history
        ch_raw = d.get("conversation_history")
        if ch_raw:
            try:
                d["conversation_history"] = json.loads(ch_raw)
            except (TypeError, ValueError):
                d["conversation_history"] = None
        else:
            d["conversation_history"] = None
        return d
    finally:
        conn.close()


def delete_record(record_id: int) -> bool:
    """删除该条 DB 记录，并删除 data/history/{record_id}/ 目录。返回是否成功。"""
    init_db()
    conn = _get_conn()
    try:
        cur = conn.execute("DELETE FROM history WHERE id = ?", (record_id,))
        conn.commit()
        if cur.rowcount == 0:
            return False
        record_dir = HISTORY_FILES_DIR / str(record_id)
        if record_dir.exists():
            shutil.rmtree(record_dir, ignore_errors=True)
        return True
    finally:
        conn.close()


def export_record(record_id: int) -> Optional[str]:
    """
    将单条记录导出为 JSON 文件（含 knowledge 文本内容），返回生成文件的绝对路径，供 Gradio 下载。
    若记录不存在则返回 None。
    """
    rec = get_record(record_id)
    if not rec:
        return None
    # 构建可序列化字典（去掉 sqlite3 的 Row 等）
    out = {
        "id": rec["id"],
        "concept": rec["concept"],
        "language": rec["language"],
        "voice_name": rec["voice_name"],
        "manim_code": rec["manim_code"],
        "srt_content": rec["srt_content"],
        "subtitle_font": rec["subtitle_font"],
        "subtitle_font_size": rec["subtitle_font_size"],
        "subtitle_font_color": rec["subtitle_font_color"],
        "subtitle_auto_wrap": rec["subtitle_auto_wrap"],
        "subtitle_alignment": rec["subtitle_alignment"],
        "saved_at": rec["saved_at"],
        "record_type": rec["record_type"],
        "agent_params": rec.get("agent_params") or {},
        "scene_durations": rec.get("scene_durations") or None,
        "conversation_history": rec.get("conversation_history") or None,
        "knowledge_content": None,
    }
    kpath = rec.get("knowledge_file_path")
    if kpath and os.path.isfile(kpath):
        try:
            with open(kpath, "r", encoding="utf-8") as f:
                out["knowledge_content"] = f.read()
        except Exception:
            out["knowledge_content"] = None
    _ensure_dirs()
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in (rec["concept"][:30] or "export"))
    filename = f"algo_history_{record_id}_{safe_name}.json"
    export_path = DATA_DIR / filename
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return str(export_path)


# 模块加载时确保表存在
init_db()
