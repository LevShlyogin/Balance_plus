#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desktop app (Tkinter) to search / add / edit / delete engineering parameters.
It implements a scalable, canonical parameter registry with:
- Canonical IDs (PID), long codes, method in long code segments, short codes
- Strict long code grammar validation
- Units model (systemUnit, allowedUnits)
- Versioning, constraints, tags, labels, descriptions
- SQLite storage with schema aligned to the ER model
- Import/export JSON для одного определения параметра

Single-file program, no third-party dependencies.
Press F1 anywhere to open built-in Help (Справка).
"""

#
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
import json
import re
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

APP_NAME = "Parameter Registry Manager"
APP_VERSION = "1.8.0"

HELP_TEXT = """
ИНСТРУКЦИЯ ПО ПРИЛОЖЕНИЮ “Parameter Registry Manager”

1) Назначение
Приложение предназначено для ведения реестра инженерных параметров: создание, поиск, редактирование, удаление, импорт/экспорт, управление единицами измерения, настройками сегментов длинного кода, короткими кодами и валидацией.

2) Быстрый старт
- Запустите приложение (создастся база registry.db рядом с .py).
- В левой панели доступен поиск и список параметров (seed-примеры уже добавлены).
- Выделите параметр слева — справа откроются вкладки редактирования.
- Нажмите F1 для Справки в любом месте.

3) Поиск и навигация (левая панель)
- Поле “Поиск” ищет по long code, short code, labels, tags, quantityKind и методике.
- Кнопки:
  • “Найти” — выполнить поиск. Нажатие Enter в поле Поиск также обновляет список.
  • “Сброс” — очистить фильтр.
  • “Добавить” — создать новый параметр (будет создан черновик long code — отредактируйте его через сегменты на вкладке “Общее”).
  • “Дублировать” — создать копию выделенного параметра (short code будет очищен, чтобы избежать конфликта).
  • “Удалить” — удалить выделенный параметр.
  • “Экспорт JSON” — выгрузить определение параметра в JSON-файл.
  • “Импорт JSON” — загрузить параметр из JSON-файла.
  • “Проверить” — запустить валидацию текущего параметра.

4) Вкладка “Общее”
- Сегменты long code — ввод полей:
  • Quantity (обяз.), Medium (обяз.),
  • Location и/или Component (хотя бы одно из них должно быть),
  • State, Statistic, Method — опционально,
  • Context — опционально (свободная строка, может содержать точки).
  Long code собирается автоматически из введённых сегментов и отображается в поле “Длинный код”.
- Методика указывается как сегмент “Method” (выпадающий список) и включается в длинный код.
- Поле “Короткий код” — строка до 32 символов, формат: [A-Za-z][A-Za-z0-9_]*.
  • Короткий код уникален в рамках одной методики (может совпадать в разных методиках).
  • Если методика не указана, уникальность не проверяется.
- Кнопка “Справочник сегментов...” — управление словарями сегментов для автосборки long code
  (добавление/редактирование/удаление: quantity/medium/location/component/state/statistic/method).
- Вид величины, тип данных и форма выбираются из выпадающих списков:
  • Вид величины (quantityKind).
  • Тип данных (dataType).
  • Форма (shape).
  Кнопка “Справочник типа данных...” — управление справочниками значений для “Вид величины”, “Тип данных” и “Форма”.
- System unit — системная единица хранения (например, K, Pa, kg/s).
- Labels/Descriptions — подписи RU/EN (в текущей версии — RU-поля).
- Tags — теги через запятую.
- Constraints — min/max (числа).
- Version — семантические поля major.minor.patch (минорная версия автоматически увеличивается при изменениях).
- Кнопка “Сохранить” — применить изменения (виды на вкладках и список слева обновятся).

5) Вкладка “Единицы”
- Управляет allowedUnits — перечнем разрешённых единиц для параметра.
- Отметьте нужные единицы галочками и нажмите “Сохранить”.
- Кнопка “Справочник единиц...” — управление справочником единиц (добавление/редактирование/удаление).
- ВНИМАНИЕ: systemUnit не обязательно должна входить в allowedUnits, но это рекомендуется. Если её снимете, появится предупреждение.

6) Вкладка “Валидация”
- Проверяет:
  • Синтаксис long code.
  • Наличие обязательных сегментов.
  • Наличие systemUnit в справочнике UNIT.
  • Непустой allowedUnits, существование всех единиц.
  • Корректность min/max.
  • Правильность формата short code и его уникальность в рамках методики.
  • Предупреждения по нераспознанным quantity/medium/method (в long code), а также по нетипичным значениям quantityKind/dataType/shape, если их нет в справочниках.

7) Правила long code (важно)
- Формат dot-path: quantity.medium.location.component.state.statistic.method.context
  (обязательны: quantity, medium и хотя бы одно из location|component; остальные — опционально)
- Допустимые символы: [a-z0-9-] в сегменте; сегменты через точку.
- Длина: сегмент ≤ 32, весь путь ≤ 200.
- Язык — английский в long code (Labels/Descriptions — RU/EN).

8) Короткий код (short code)
- Формат: [A-Za-z][A-Za-z0-9_]{0,31} (до 32 символов).
- Уникален в пределах одной методики (method).
- Можно не указывать (пусто) — тогда уникальность не проверяется.

9) Импорт / Экспорт
- Экспорт JSON — сохраняет полное определение параметра (включая method и shortCode).
- Импорт JSON — добавляет новый параметр (PID создаётся новый). При конфликте shortCode в той же методике будет ошибка.

10) База данных и резервное копирование
- Все данные хранятся в SQLite-файле registry.db рядом с приложением.
- Для резервной копии — просто скопируйте registry.db.
- При первой загрузке создаются демонстрационные параметры и минимальные словари сегментов/единиц/типов/форм.

11) Типичные сценарии (примеры)
- Регистрация параметра:
  1. Кнопка “Добавить” (слева) — будет создан черновик параметра.
  2. На вкладке “Общее” заполните сегменты long code (quantity, medium, …, method) — long code соберётся автоматически.
  3. При необходимости укажите короткий код (short code). Если задана методика — будет проверена уникальность короткого кода в её рамках.
  4. Заполните QuantityKind, System unit, Labels и др.
  5. На вкладке “Единицы” отметьте allowedUnits.
  6. На вкладке “Валидация” убедитесь, что ошибок нет, и сохраните изменения.
- Редактирование параметра:
  1. Выберите параметр слева.
  2. Вносите правки на вкладке “Общее” (включая short code) и нажмите “Сохранить”.
  3. При необходимости обновите allowedUnits.
- Удаление параметра:
  1. Выберите параметр слева.
  2. Нажмите “Удалить” и подтвердите действие.

12) Горячие клавиши
- F1 — открыть Справку.
- Enter в поле “Поиск” — выполнить поиск.

13) Ограничения текущей версии
- Нет конвертации единиц.
- Валидация long code выполняет синтаксические и базовые семантические проверки.
- Отсутствует параллельный доступ и синхронизация (SQLite для одиночного пользователя).
- Нет сетевого API (REST/GraphQL) — только локальный GUI и локальная БД.

Удачной работы!
""".strip()


# ------------------------- Helpers -------------------------

def now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def gen_uuid() -> str:
    return str(uuid.uuid4())


def safe_json_loads(s: Optional[str], default):
    try:
        if s is None:
            return default
        return json.loads(s)
    except Exception:
        return default


def safe_json_dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9\-]", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s


SHORT_CODE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,31}$")


# ------------------------- Seed dictionaries (for initial DB fill) -------------------------

SEED_QUANTITIES = {
    "temperature", "pressure", "mass-flow", "density", "enthalpy",
    "efficiency", "power", "speed", "volume",
}

SEED_MEDIUMS = {
    "air", "gas", "water", "steam"
}

SEED_LOCATIONS = {
    "inlet", "outlet", "ambient"
    # plus node-*, section-*, station-*
}

SEED_COMPONENTS = {
    "compressor", "turbine", "pipe", "valve",
}

SEED_STATES = {"static", "total", "wet", "dry"}
SEED_STATISTICS = {"mean", "min", "max", "std", "instant", "integral"}

SEED_METHODS = {"poly", "mapfit", "default"}

SEED_DATA_TYPES = {"float64", "int64", "int32", "string", "bool"}
SEED_SHAPES = {"scalar", "vector", "matrix", "timeseries"}

SEED_QUANTITY_KINDS = {
    "thermodynamic parameter", "geometry",
    "thermodynamic-temperature", "pressure", "mass-flow"
}


# ------------------------- Database -------------------------

class Database:
    def __init__(self, path: str = "registry.db"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self._seed_units()
        self._seed_sequences()
        self._seed_segments()
        self._seed_data_dicts()
        self._seed_examples()

    def _execute(self, sql: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()
        return cur

    def _init_schema(self):
        self._execute("PRAGMA foreign_keys = ON;")
        # PARAMETER
        self._execute("""
        CREATE TABLE IF NOT EXISTS PARAMETER (
            id TEXT PRIMARY KEY,
            long_code TEXT UNIQUE COLLATE NOCASE,
            quantity_kind TEXT,
            data_type TEXT,
            shape TEXT,
            system_unit TEXT,
            method_name TEXT,
            short_code TEXT,
            labels TEXT, -- json
            description TEXT, -- json
            tags TEXT, -- json
            constraints TEXT, -- json
            version_major INTEGER,
            version_minor INTEGER,
            version_patch INTEGER
        );
        """)
        # MIGRATION: ensure columns exist in old DBs
        try:
            cur = self._execute("PRAGMA table_info(PARAMETER)")
            cols = {r["name"] for r in cur.fetchall()}
            if "method_name" not in cols:
                self._execute("ALTER TABLE PARAMETER ADD COLUMN method_name TEXT;")
            if "short_code" not in cols:
                self._execute("ALTER TABLE PARAMETER ADD COLUMN short_code TEXT;")
        except Exception:
            pass
        # Unique index for (method_name, short_code)
        self._execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_param_method_short
        ON PARAMETER(method_name, short_code);
        """)

        # UNIT
        self._execute("""
        CREATE TABLE IF NOT EXISTS UNIT (
            code TEXT PRIMARY KEY,
            dimension TEXT
        );
        """)
        # PARAMETER_ALLOWED_UNIT
        self._execute("""
        CREATE TABLE IF NOT EXISTS PARAMETER_ALLOWED_UNIT (
            parameter_id TEXT,
            unit_code TEXT,
            PRIMARY KEY (parameter_id, unit_code),
            FOREIGN KEY(parameter_id) REFERENCES PARAMETER(id) ON DELETE CASCADE,
            FOREIGN KEY(unit_code) REFERENCES UNIT(code) ON DELETE CASCADE
        );
        """)
        # Справочник сегментов long code
        self._execute("""
        CREATE TABLE IF NOT EXISTS CODE_SEGMENT (
            kind TEXT NOT NULL,    -- quantity | medium | location | component | state | statistic | method
            value TEXT NOT NULL,
            label TEXT,
            notes TEXT,
            PRIMARY KEY (kind, value)
        );
        """)
        # Универсальный справочник значений для quantityKind/dataType/shape
        self._execute("""
        CREATE TABLE IF NOT EXISTS DATA_DICT (
            kind TEXT NOT NULL,    -- quantity_kind | data_type | shape
            value TEXT NOT NULL,
            label TEXT,
            notes TEXT,
            PRIMARY KEY (kind, value)
        );
        """)
        # Последовательности
        self._execute("""
        CREATE TABLE IF NOT EXISTS SEQ (
            name TEXT PRIMARY KEY,
            value INTEGER
        );
        """)

    def _seed_sequences(self):
        cur = self._execute("SELECT value FROM SEQ WHERE name='param_seq'")
        row = cur.fetchone()
        if row is None:
            self._execute("INSERT INTO SEQ(name, value) VALUES (?, ?)", ("param_seq", 0))

    def _seed_units(self):
        # Minimal unit set
        units = [
            ("К", "temperature"),
            ("°С", "temperature"),
            ("F", "temperature"),
            ("Па", "pressure"),
            ("кПа", "pressure"),
            ("бар", "pressure"),
            ("МПа", "pressure"),
            ("кг/с", "mass-flow"),
            ("кг/ч", "mass-flow"),
            ("гр/с", "mass-flow")
        ]
        for code, dim in units:
            cur = self._execute("SELECT code FROM UNIT WHERE code=?", (code,))
            if cur.fetchone() is None:
                self._execute("INSERT INTO UNIT(code, dimension) VALUES (?, ?)", (code, dim))

    def next_param_pid(self) -> str:
        self._execute("UPDATE SEQ SET value = value + 1 WHERE name='param_seq'")
        cur = self._execute("SELECT value FROM SEQ WHERE name='param_seq'")
        v = cur.fetchone()["value"]
        return f"PRM-{v:08d}"

    def _seed_segments(self):
        # Seed only if empty
        cur = self._execute("SELECT COUNT(*) AS cnt FROM CODE_SEGMENT")
        if cur.fetchone()["cnt"] > 0:
            # ensure method kind exists and seeded minimally
            for m in sorted(SEED_METHODS):
                self._execute(
                    "INSERT OR IGNORE INTO CODE_SEGMENT(kind, value, label, notes) VALUES (?, ?, ?, ?)",
                    ("method", m, "", "")
                )
            return

        def ins(kind: str, items: set):
            for v in sorted(items):
                self._execute(
                    "INSERT OR IGNORE INTO CODE_SEGMENT(kind, value, label, notes) VALUES (?, ?, ?, ?)",
                    (kind, v, "", "")
                )

        ins("quantity", SEED_QUANTITIES)
        ins("medium", SEED_MEDIUMS)
        ins("location", SEED_LOCATIONS)
        ins("component", SEED_COMPONENTS)
        ins("state", SEED_STATES)
        ins("statistic", SEED_STATISTICS)
        ins("method", SEED_METHODS)

    # DATA_DICT helpers
    def _seed_data_dicts(self):
        # quantity_kind
        for v in sorted(SEED_QUANTITY_KINDS):
            self._execute("INSERT OR IGNORE INTO DATA_DICT(kind, value, label, notes) VALUES (?, ?, ?, ?)",
                          ("quantity_kind", v, "", ""))
        # data_type
        for v in sorted(SEED_DATA_TYPES):
            self._execute("INSERT OR IGNORE INTO DATA_DICT(kind, value, label, notes) VALUES (?, ?, ?, ?)",
                          ("data_type", v, "", ""))
        # shape
        for v in sorted(SEED_SHAPES):
            self._execute("INSERT OR IGNORE INTO DATA_DICT(kind, value, label, notes) VALUES (?, ?, ?, ?)",
                          ("shape", v, "", ""))

    def list_segment_values(self, kind: str) -> List[str]:
        cur = self._execute("SELECT value FROM CODE_SEGMENT WHERE kind=? ORDER BY value", (kind,))
        return [r["value"] for r in cur.fetchall()]

    def list_segments(self, kind: str) -> List[sqlite3.Row]:
        cur = self._execute("SELECT kind, value, label, notes FROM CODE_SEGMENT WHERE kind=? ORDER BY value", (kind,))
        return cur.fetchall()

    def add_segment(self, kind: str, value: str, label: str = "", notes: str = ""):
        self._execute(
            "INSERT INTO CODE_SEGMENT(kind, value, label, notes) VALUES (?, ?, ?, ?)",
            (kind, value, label, notes)
        )

    def update_segment(self, kind: str, old_value: str, new_value: str, label: str = "", notes: str = ""):
        self._execute(
            "UPDATE CODE_SEGMENT SET value=?, label=?, notes=? WHERE kind=? AND value=?",
            (new_value, label, notes, kind, old_value)
        )

    def delete_segment(self, kind: str, value: str):
        self._execute("DELETE FROM CODE_SEGMENT WHERE kind=? AND value=?", (kind, value))

    # DATA_DICT methods
    def list_data_dict_values(self, kind: str) -> List[str]:
        cur = self._execute("SELECT value FROM DATA_DICT WHERE kind=? ORDER BY value", (kind,))
        return [r["value"] for r in cur.fetchall()]

    def list_data_dict(self, kind: str) -> List[sqlite3.Row]:
        cur = self._execute("SELECT kind, value, label, notes FROM DATA_DICT WHERE kind=? ORDER BY value", (kind,))
        return cur.fetchall()

    def add_data_dict(self, kind: str, value: str, label: str = "", notes: str = ""):
        self._execute("INSERT INTO DATA_DICT(kind, value, label, notes) VALUES (?, ?, ?, ?)", (kind, value, label, notes))

    def update_data_dict(self, kind: str, old_value: str, new_value: str, label: str = "", notes: str = ""):
        self._execute("UPDATE DATA_DICT SET value=?, label=?, notes=? WHERE kind=? AND value=?",
                      (new_value, label, notes, kind, old_value))

    def delete_data_dict(self, kind: str, value: str):
        self._execute("DELETE FROM DATA_DICT WHERE kind=? AND value=?", (kind, value))

    def rename_unit_with_dimension(self, old_code: str, new_code: str, dimension: str):
        if old_code == new_code:
            self._execute("UPDATE UNIT SET dimension=? WHERE code=?", (dimension, old_code))
            return
        cur_old = self._execute("SELECT code FROM UNIT WHERE code=?", (old_code,))
        if not cur_old.fetchone():
            raise ValueError(f"Единица '{old_code}' не найдена")
        cur_new = self._execute("SELECT code FROM UNIT WHERE code=?", (new_code,))
        if cur_new.fetchone():
            raise ValueError(f"Единица с кодом '{new_code}' уже существует")

        self._execute("INSERT INTO UNIT(code, dimension) VALUES (?, ?)", (new_code, dimension))
        # Update references
        self._execute("UPDATE PARAMETER SET system_unit=? WHERE system_unit=?", (new_code, old_code))
        self._execute("UPDATE PARAMETER_ALLOWED_UNIT SET unit_code=? WHERE unit_code=?", (new_code, old_code))
        # Remove old
        self._execute("DELETE FROM UNIT WHERE code=?", (old_code,))

    def _seed_examples(self):
        # Seed example parameters if DB is empty
        cur = self._execute("SELECT COUNT(*) AS cnt FROM PARAMETER")
        if cur.fetchone()["cnt"] > 0:
            return

        # Example 1: Inlet temperature
        pid1 = self.next_param_pid()
        self._execute("""
        INSERT INTO PARAMETER(id, long_code, quantity_kind, data_type, shape, system_unit, method_name, short_code, labels, description,
                              tags, constraints, version_major, version_minor, version_patch)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pid1,
            "temperature.gas.inlet.compressor.k-101.total.mean.poly",
            "thermodynamic-temperature",
            "float64",
            "scalar",
            "K",
            "poly",
            "T_in",
            safe_json_dumps({"en": "Inlet total temperature K-101", "ru": "Температура на входе (полная) K-101"}),
            safe_json_dumps({"en": "", "ru": "Полная температура газа на входе компрессора K-101"}),
            safe_json_dumps(["thermo", "compressor", "inlet"]),
            safe_json_dumps({"min": 0, "max": 2000}),
            1, 0, 0
        ))
        for u in ["K", "Cel", "degF"]:
            self._execute("INSERT INTO PARAMETER_ALLOWED_UNIT(parameter_id, unit_code) VALUES (?, ?)", (pid1, u))

        # Example 2: Outlet pressure
        pid2 = self.next_param_pid()
        self._execute("""
        INSERT INTO PARAMETER(id, long_code, quantity_kind, data_type, shape, system_unit, method_name, short_code, labels, description,
                              tags, constraints, version_major, version_minor, version_patch)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pid2,
            "pressure.gas.outlet.compressor.k-101.static.mean.mapfit",
            "pressure",
            "float64",
            "scalar",
            "Pa",
            "mapfit",
            "P_out",
            safe_json_dumps({"en": "Outlet static pressure K-101", "ru": "Давление на выходе (статическое) K-101"}),
            safe_json_dumps({"en": "", "ru": ""}),
            safe_json_dumps(["compressor", "outlet"]),
            safe_json_dumps({"min": 0, "max": 1e9}),
            1, 0, 0
        ))
        for u in ["Pa", "kPa", "bar", "MPa"]:
            self._execute("INSERT INTO PARAMETER_ALLOWED_UNIT(parameter_id, unit_code) VALUES (?, ?)", (pid2, u))

        # Example 3: Mass-flow
        pid3 = self.next_param_pid()
        self._execute("""
        INSERT INTO PARAMETER(id, long_code, quantity_kind, data_type, shape, system_unit, method_name, short_code, labels, description,
                              tags, constraints, version_major, version_minor, version_patch)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pid3,
            "mass-flow.gas.inlet.compressor.k-101.mean.poly",
            "mass-flow",
            "float64",
            "scalar",
            "kg/s",
            "poly",
            "mdot_in",
            safe_json_dumps({"en": "Inlet mass flow K-101", "ru": "Массовый расход на входе K-101"}),
            safe_json_dumps({"en": "", "ru": ""}),
            safe_json_dumps(["compressor", "inlet"]),
            safe_json_dumps({"min": 0, "max": 1e5}),
            1, 0, 0
        ))
        for u in ["kg/s", "kg/h", "g/s", "lb/s"]:
            self._execute("INSERT INTO PARAMETER_ALLOWED_UNIT(parameter_id, unit_code) VALUES (?, ?)", (pid3, u))


# ------------------------- Parameter Registry -------------------------

class ParameterRegistry:
    LONG_CODE_RE = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)*$")

    def __init__(self, db: Database):
        self.db = db
        self._cache = {"long2pid": {}, "pid2meta": {}}
        self.refresh_cache()

    def refresh_cache(self):
        # long -> pid
        cur = self.db._execute("SELECT id, long_code, system_unit FROM PARAMETER")
        self._cache["long2pid"] = {}
        self._cache["pid2meta"] = {}
        for row in cur.fetchall():
            self._cache["long2pid"][row["long_code"]] = row["id"]
            self._cache["pid2meta"][row["id"]] = {"systemUnit": row["system_unit"], "longCode": row["long_code"]}

    def getById(self, pid: str) -> Optional[sqlite3.Row]:
        cur = self.db._execute("SELECT * FROM PARAMETER WHERE id=?", (pid,))
        return cur.fetchone()

    def getByLongCode(self, code: str) -> Optional[sqlite3.Row]:
        cur = self.db._execute("SELECT * FROM PARAMETER WHERE long_code=?", (code,))
        return cur.fetchone()

    def list(self, search: str = "") -> List[sqlite3.Row]:
        search = (search or "").strip()
        if not search:
            cur = self.db._execute("SELECT * FROM PARAMETER ORDER BY long_code")
            return cur.fetchall()
        like = f"%{search.lower()}%"
        cur = self.db._execute("""
            SELECT * FROM PARAMETER
            WHERE LOWER(long_code) LIKE ?
               OR LOWER(IFNULL(short_code,'')) LIKE ?
               OR LOWER(labels) LIKE ?
               OR LOWER(tags) LIKE ?
               OR LOWER(quantity_kind) LIKE ?
               OR LOWER(IFNULL(method_name,'')) LIKE ?
            ORDER BY long_code
        """, (like, like, like, like, like, like))
        return cur.fetchall()

    def allowedUnits(self, pid: str) -> List[str]:
        cur = self.db._execute("SELECT unit_code FROM PARAMETER_ALLOWED_UNIT WHERE parameter_id=? ORDER BY unit_code", (pid,))
        return [r["unit_code"] for r in cur.fetchall()]

    def systemUnit(self, pid: str) -> str:
        cur = self.db._execute("SELECT system_unit FROM PARAMETER WHERE id=?", (pid,))
        row = cur.fetchone()
        if not row:
            raise KeyError("Параметр не найден")
        return row["system_unit"]

    def is_short_code_unique(self, method: Optional[str], short_code: Optional[str], exclude_pid: Optional[str] = None) -> bool:
        sc = (short_code or "").strip()
        m = (method or "").strip()
        if sc == "" or m == "":
            # Uniqueness not enforced when method or short code is empty
            return True
        if exclude_pid:
            cur = self.db._execute(
                "SELECT id FROM PARAMETER WHERE method_name=? AND short_code=? AND id<>?",
                (m, sc, exclude_pid)
            )
        else:
            cur = self.db._execute(
                "SELECT id FROM PARAMETER WHERE method_name=? AND short_code=?",
                (m, sc)
            )
        return cur.fetchone() is None

    def create_parameter(self, param: Dict[str, Any]) -> str:
        # pre-check short code uniqueness when provided
        if not self.is_short_code_unique(param.get("method"), param.get("shortCode")):
            raise ValueError("Короткий код уже используется в этой методике")

        pid = self.db.next_param_pid()
        # Начинаем всегда с 1.0.0 (автоматическая регистрация версий)
        vmaj, vmin, vpat = 1, 0, 0
        self.db._execute("""
        INSERT INTO PARAMETER(id, long_code, quantity_kind, data_type, shape, system_unit, method_name, short_code, labels, description,
                              tags, constraints, version_major, version_minor, version_patch)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pid,
            param["longCode"],
            param.get("quantityKind") or "",
            param.get("dataType") or "float64",
            param.get("shape") or "scalar",
            param["systemUnit"],
            param.get("method") or None,
            (param.get("shortCode") or None),
            safe_json_dumps(param.get("labels") or {}),
            safe_json_dumps(param.get("description") or {}),
            safe_json_dumps(param.get("tags") or []),
            safe_json_dumps(param.get("constraints") or {}),
            vmaj, vmin, vpat
        ))
        for u in param.get("allowedUnits", []):
            self.db._execute("INSERT INTO PARAMETER_ALLOWED_UNIT(parameter_id, unit_code) VALUES (?, ?)", (pid, u))
        self.refresh_cache()
        return pid

    def update_parameter(self, pid: str, param: Dict[str, Any]) -> None:
        row = self.getById(pid)
        if not row:
            raise KeyError("Параметр не найден")

        # pre-check short code uniqueness when provided
        if not self.is_short_code_unique(param.get("method"), param.get("shortCode"), exclude_pid=pid):
            raise ValueError("Короткий код уже используется в этой методике")

        allowed_old = sorted(self.allowedUnits(pid))

        def norm_labels(x):
            return safe_json_loads(x, {}) if isinstance(x, str) else (x or {})

        def norm_descr(x):
            return safe_json_loads(x, {}) if isinstance(x, str) else (x or {})

        def norm_tags(x):
            t = safe_json_loads(x, []) if isinstance(x, str) else (x or [])
            return sorted(set(map(str, t)))

        def norm_constraints(x):
            return safe_json_loads(x, {}) if isinstance(x, str) else (x or {})

        old_snap = {
            "longCode": row["long_code"],
            "quantityKind": row["quantity_kind"],
            "dataType": row["data_type"],
            "shape": row["shape"],
            "systemUnit": row["system_unit"],
            "method": row["method_name"] or "",
            "shortCode": row["short_code"] or "",
            "labels": norm_labels(row["labels"]),
            "description": norm_descr(row["description"]),
            "tags": norm_tags(row["tags"]),
            "constraints": norm_constraints(row["constraints"]),
            "allowedUnits": allowed_old,
        }

        new_snap = {
            "longCode": param["longCode"],
            "quantityKind": param.get("quantityKind") or "",
            "dataType": param.get("dataType") or "float64",
            "shape": param.get("shape") or "scalar",
            "systemUnit": param["systemUnit"],
            "method": param.get("method") or "",
            "shortCode": param.get("shortCode") or "",
            "labels": param.get("labels") or {},
            "description": param.get("description") or {},
            "tags": sorted(set(map(str, param.get("tags") or []))),
            "constraints": param.get("constraints") or {},
            "allowedUnits": sorted(param.get("allowedUnits") or []),
        }

        changed = safe_json_dumps(old_snap) != safe_json_dumps(new_snap)

        # Авто‑версионирование: +0.1 при изменениях, patch = 0
        vmaj = int(row["version_major"] or 1)
        vmin = int(row["version_minor"] or 0)
        vpat = 0
        if changed:
            vmin += 1

        self.db._execute("""
        UPDATE PARAMETER SET 
            long_code=?, quantity_kind=?, data_type=?, shape=?, system_unit=?, method_name=?, short_code=?, labels=?, description=?,
            tags=?, constraints=?, version_major=?, version_minor=?, version_patch=?
        WHERE id=?
        """, (
            param["longCode"],
            param.get("quantityKind") or "",
            param.get("dataType") or "float64",
            param.get("shape") or "scalar",
            param["systemUnit"],
            param.get("method") or None,
            (param.get("shortCode") or None),
            safe_json_dumps(param.get("labels") or {}),
            safe_json_dumps(param.get("description") or {}),
            safe_json_dumps(param.get("tags") or []),
            safe_json_dumps(param.get("constraints") or {}),
            vmaj, vmin, vpat,
            pid
        ))
        self.db._execute("DELETE FROM PARAMETER_ALLOWED_UNIT WHERE parameter_id=?", (pid,))
        for u in param.get("allowedUnits", []):
            self.db._execute("INSERT INTO PARAMETER_ALLOWED_UNIT(parameter_id, unit_code) VALUES (?, ?)", (pid, u))
        self.refresh_cache()

    def delete_parameter(self, pid: str):
        self.db._execute("DELETE FROM PARAMETER WHERE id=?", (pid,))
        self.refresh_cache()

    def validate_long_code(self, code: str) -> Tuple[List[str], List[str]]:
        errors = []
        warnings = []
        code = (code or "").strip()
        if not code:
            errors.append("longCode пуст")
            return errors, warnings

        if len(code) > 200:
            errors.append("longCode превышает максимальную длину 200")

        if not self.LONG_CODE_RE.match(code):
            errors.append("longCode должен содержать только сегменты [a-z0-9-], разделённые точками '.'")

        segments = code.split(".")
        for s in segments:
            if len(s) > 32:
                errors.append(f"Сегмент '{s}' длинее 32 символов")

        if len(segments) < 3:
            errors.append("longCode должен иметь минимум 3 сегмента (quantity.medium.[location|component]...)")

        # DB-driven vocabularies
        quantities = set(self.db.list_segment_values("quantity"))
        mediums = set(self.db.list_segment_values("medium"))
        locations = set(self.db.list_segment_values("location"))
        components = set(self.db.list_segment_values("component"))
        methods = set(self.db.list_segment_values("method"))

        quantity = segments[0] if segments else ""
        if quantity not in quantities:
            warnings.append(f"Неизвестная величина '{quantity}' (рассмотрите использование контролируемого словаря)")

        if len(segments) >= 2:
            medium = segments[1]
            if not (medium in mediums or medium.startswith("mixture-")):
                warnings.append(f"Среда '{medium}' не распознана (при необходимости отредактируйте через 'Справочник сегментов...')")
        else:
            errors.append("Второй сегмент (medium) обязателен")

        has_location = any(
            s in locations or s.startswith("node-") or s.startswith("section-") or s.startswith("station-") for s in segments[2:]
        )
        has_component = any(
            s in components for s in segments[2:]
        )
        if not (has_location or has_component):
            errors.append("longCode должен включать сегмент 'location' (inlet/outlet/...) или 'component' (compressor/pipe/...)")

        # Method optional — предупреждение даётся в validate_parameter
        _ = methods  # placeholder

        return errors, warnings

    def validate_parameter(self, pid: str) -> Dict[str, Any]:
        cur = self.db._execute("SELECT * FROM PARAMETER WHERE id=?", (pid,))
        p = cur.fetchone()
        if not p:
            return {"ok": False, "errors": ["Параметр не найден"], "warnings": []}

        errors, warnings = self.validate_long_code(p["long_code"])

        # Units existence
        cur = self.db._execute("SELECT 1 FROM UNIT WHERE code=?", (p["system_unit"],))
        if not cur.fetchone():
            errors.append(f"Системная единица '{p['system_unit']}' не найдена в справочнике UNIT")

        cur = self.db._execute("SELECT unit_code FROM PARAMETER_ALLOWED_UNIT WHERE parameter_id=?", (pid,))
        allowed = [r["unit_code"] for r in cur.fetchall()]
        if not allowed:
            errors.append("Список allowedUnits не должен быть пустым")
        if allowed and p["system_unit"] not in allowed:
            warnings.append(f"systemUnit '{p['system_unit']}' отсутствует в allowedUnits")

        for u in allowed:
            c = self.db._execute("SELECT 1 FROM UNIT WHERE code=?", (u,))
            if not c.fetchone():
                errors.append(f"Разрешённая единица '{u}' отсутствует в справочнике UNIT")

        # Справочники dataType/shape/quantityKind
        types = set(self.db.list_data_dict_values("data_type"))
        shapes = set(self.db.list_data_dict_values("shape"))
        qkinds = set(self.db.list_data_dict_values("quantity_kind"))
        if p["data_type"] not in types:
            warnings.append(f"Нетипичный dataType '{p['data_type']}' (справочник: {sorted(types)})")
        if p["shape"] not in shapes:
            warnings.append(f"Нетипичная форма '{p['shape']}' (справочник: {sorted(shapes)})")
        if p["quantity_kind"] and p["quantity_kind"] not in qkinds:
            warnings.append(f"Нетипичный quantityKind '{p['quantity_kind']}' (справочник: {sorted(qkinds)})")

        # Предупреждение по методике
        methods = set(self.db.list_segment_values("method"))
        if (p["method_name"] or "") and p["method_name"] not in methods:
            warnings.append(f"Нетипичная методика '{p['method_name']}' (справочник: {sorted(methods)})")

        # Валидация short code
        sc = (p["short_code"] or "").strip()
        mn = (p["method_name"] or "").strip()
        if sc:
            if not SHORT_CODE_RE.match(sc):
                errors.append("shortCode должен начинаться с буквы и содержать до 32 символов [A-Za-z0-9_]")
            elif mn and not self.is_short_code_unique(mn, sc, exclude_pid=pid):
                errors.append(f"shortCode '{sc}' уже используется в методике '{mn}'")

        constraints = safe_json_loads(p["constraints"], {})
        try:
            mnv = constraints.get("min", None)
            mxv = constraints.get("max", None)
            if mnv is not None and mxv is not None:
                if float(mnv) > float(mxv):
                    errors.append("constraints.min > constraints.max")
        except Exception:
            warnings.append("constraints min/max — не числа")

        return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings}


# ------------------------- GUI Components -------------------------

class MethodChoiceDialog(tk.Toplevel):
    def __init__(self, master, methods: List[str]):
        super().__init__(master)
        self.title("Выбор методики")
        self.transient(master)
        self.grab_set()
        self.result: Optional[str] = None

        ttk.Label(self, text="Методика:").pack(anchor="w", padx=10, pady=(10, 4))
        self.var = tk.StringVar(value=methods[0] if methods else "")
        self.combo = ttk.Combobox(self, textvariable=self.var, values=methods, state="readonly", width=30)
        self.combo.pack(fill="x", padx=10)
        self.combo.focus_set()

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=10, pady=10)
        ttk.Button(btns, text="OK", command=self._ok).pack(side="right")
        ttk.Button(btns, text="Отмена", command=self._cancel).pack(side="right", padx=(0, 6))

        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self._cancel())

    def _ok(self):
        self.result = self.var.get().strip()
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class ParameterListFrame(ttk.Frame):
    def __init__(self, master, registry: ParameterRegistry, on_select):
        super().__init__(master)
        self.registry = registry
        self.on_select = on_select

        self.search_var = tk.StringVar()
        self._build()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=4, pady=4)

        ttk.Label(top, text="Поиск").pack(side="left")
        ent = ttk.Entry(top, textvariable=self.search_var, width=30)
        ent.pack(side="left", padx=4)
        ent.bind("<Return>", lambda e: self.refresh())

        ttk.Button(top, text="Найти", command=self.refresh).pack(side="left")
        ttk.Button(top, text="Сброс", command=self._clear_search).pack(side="left", padx=2)

        # Container with scrollbars
        tree_container = ttk.Frame(self)
        tree_container.pack(fill="both", expand=True, padx=4, pady=4)

        # New columns order with 'Методика' after PID and 'Короткий код' after 'Длинный код'
        columns = ("pid", "method", "qk", "long", "short", "sys", "range", "dtype")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=20)
        # Headings
        self.tree.heading("pid", text="PID")
        self.tree.heading("method", text="Методика")
        self.tree.heading("qk", text="Вид величины")
        self.tree.heading("long", text="Длинный код")
        self.tree.heading("short", text="Короткий код")
        self.tree.heading("sys", text="Системная ед.")
        self.tree.heading("range", text="Диапазон")
        self.tree.heading("dtype", text="Тип данных")
        # Column widths (enable horizontal scroll if overflow)
        self.tree.column("pid", width=120, anchor="w")
        self.tree.column("method", width=160, anchor="w")
        self.tree.column("qk", width=180, anchor="w")
        self.tree.column("long", width=600, anchor="w")
        self.tree.column("short", width=180, anchor="w")
        self.tree.column("sys", width=120, anchor="w")
        self.tree.column("range", width=160, anchor="w")
        self.tree.column("dtype", width=120, anchor="w")

        # Scrollbars
        yscroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        # Layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=4, pady=2)
        self.add_btn = ttk.Button(btns, text="Добавить", command=self._add)
        self.add_btn.pack(side="left")
        self.dup_btn = ttk.Button(btns, text="Дублировать", command=self._duplicate)
        self.dup_btn.pack(side="left", padx=4)
        self.del_btn = ttk.Button(btns, text="Удалить", command=self._delete)
        self.del_btn.pack(side="left", padx=4)
        self.exp_btn = ttk.Button(btns, text="Экспорт JSON", command=self._export)
        self.exp_btn.pack(side="left", padx=4)
        self.imp_btn = ttk.Button(btns, text="Импорт JSON", command=self._import)
        self.imp_btn.pack(side="left", padx=4)
        # New button: Export to Markdown
        self.exp_md_btn = ttk.Button(btns, text="Экспорт в MD", command=self._export_md)
        self.exp_md_btn.pack(side="left", padx=4)
        # Removed: 'Проверить' button per requirements

        self.refresh()

    def _clear_search(self):
        self.search_var.set("")
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = self.registry.list(self.search_var.get())
        for r in rows:
            constr = safe_json_loads(r["constraints"], {})
            mn = constr.get("min", "")
            mx = constr.get("max", "")
            rng = f"{'' if mn is None else mn} - {'' if mx is None else mx}"
            self.tree.insert("", "end", iid=r["id"], values=(
                r["id"],
                r["method_name"] or "",
                r["quantity_kind"],
                r["long_code"],
                r["short_code"] or "",
                r["system_unit"],
                rng,
                r["data_type"],
            ))

    def _on_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        pid = sel[0]
        self.on_select(pid)

    def _add(self):
        draft_long = f"draft.item.{gen_uuid().split('-')[0]}"
        # Choose a default existing unit from UNIT dictionary (no prompt)
        cur = self.registry.db._execute("SELECT code FROM UNIT ORDER BY code LIMIT 1")
        row = cur.fetchone()
        su = row["code"] if row else ""
        param = {
            "longCode": draft_long,
            "quantityKind": "",
            "dataType": "float64",
            "shape": "scalar",
            "systemUnit": su,
            "method": "",
            "shortCode": "",
            "labels": {"ru": ""},
            "description": {"ru": ""},
            "tags": [],
            "constraints": {},
            "allowedUnits": [su] if su else [],
        }
        try:
            new_pid = self.registry.create_parameter(param)
            messagebox.showinfo("OK", f"Создан черновик параметра {new_pid}")
            self.refresh()
            self.tree.selection_set(new_pid)
            self.on_select(new_pid)
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось создать параметр:\n{ex}")

    def _duplicate(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите параметр для дублирования")
            return
        pid = sel[0]
        row = self.registry.getById(pid)
        if not row:
            return
        long_new = row["long_code"] + "-copy"
        allowed = [u for u in self.registry.allowedUnits(pid)]
        param = {
            "longCode": long_new,
            "quantityKind": row["quantity_kind"],
            "dataType": row["data_type"],
            "shape": row["shape"],
            "systemUnit": row["system_unit"],
            "method": row["method_name"] or "",
            "shortCode": "",  # очистим, чтобы не конфликтовать
            "labels": safe_json_loads(row["labels"], {}),
            "description": safe_json_loads(row["description"], {}),
            "tags": safe_json_loads(row["tags"], []),
            "constraints": safe_json_loads(row["constraints"], {}),
            "allowedUnits": allowed,
        }
        try:
            new_pid = self.registry.create_parameter(param)
            messagebox.showinfo("OK", f"Создан дубликат {new_pid}")
            self.refresh()
            self.tree.selection_set(new_pid)
            self.on_select(new_pid)
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось создать дубликат:\n{ex}")

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите параметр для удаления")
            return
        pid = sel[0]
        if messagebox.askyesno("Подтверждение", "Удалить выбранный параметр?"):
            try:
                self.registry.delete_parameter(pid)
                self.refresh()
                self.on_select(None)
            except Exception as ex:
                messagebox.showerror("Ошибка", f"Не удалось удалить:\n{ex}")

    def _export(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите параметр для экспорта")
            return
        pid = sel[0]
        row = self.registry.getById(pid)
        if not row:
            return
        allowed = self.registry.allowedUnits(pid)

        # Экспортируем только RU-поля названия/описания
        labels_all = safe_json_loads(row["labels"], {})
        descr_all = safe_json_loads(row["description"], {})
        labels_ru = {"ru": labels_all.get("ru", "")}
        descr_ru = {"ru": descr_all.get("ru", "")}

        param_json = {
            "id": row["id"],
            "longCode": row["long_code"],
            "labels": labels_ru,
            "description": descr_ru,
            "quantityKind": row["quantity_kind"],
            "dataType": row["data_type"],
            "shape": row["shape"],
            "systemUnit": row["system_unit"],
            "method": row["method_name"] or "",
            "shortCode": row["short_code"] or "",
            "allowedUnits": allowed,
            "tags": safe_json_loads(row["tags"], []),
            "constraints": safe_json_loads(row["constraints"], {}),
            "version": f"{row['version_major']}.{row['version_minor']}.{row['version_patch']}",
        }
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], title="Сохранить параметр в JSON")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(param_json, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("OK", f"Сохранено: {path}")
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{ex}")

    def _import(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")], title="Импорт параметра из JSON")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                param_json = json.load(f)
            # Версия игнорируется при создании (автоверсионирование начнёт с 1.0)
            method = param_json.get("method") or ""
            short_code = param_json.get("shortCode") or ""
            # Предварительная проверка уникальности (если метод и shortCode заданы)
            if short_code and method and not self.registry.is_short_code_unique(method, short_code):
                messagebox.showerror("Ошибка импорта", f"shortCode '{short_code}' уже используется в методике '{method}'")
                return
            param = {
                "longCode": param_json["longCode"],
                "quantityKind": param_json.get("quantityKind") or "",
                "dataType": param_json.get("dataType") or "float64",
                "shape": param_json.get("shape") or "scalar",
                "systemUnit": param_json["systemUnit"],
                "method": method,
                "shortCode": short_code,
                "labels": {"ru": (param_json.get("labels") or {}).get("ru", "")},
                "description": {"ru": (param_json.get("description") or {}).get("ru", "")},
                "tags": param_json.get("tags") or [],
                "constraints": param_json.get("constraints") or {},
                "allowedUnits": param_json.get("allowedUnits") or [param_json["systemUnit"]],
            }
            new_pid = self.registry.create_parameter(param)
            messagebox.showinfo("OK", f"Импортирован параметр {new_pid}")
            self.refresh()
            self.tree.selection_set(new_pid)
            self.on_select(new_pid)
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось импортировать:\n{ex}")

    def _export_md(self):
        # Build list of methods from dictionary; if empty, also scan existing parameters
        methods = sorted(set(self.registry.db.list_segment_values("method")))
        if not methods:
            cur = self.registry.db._execute("SELECT DISTINCT method_name FROM PARAMETER WHERE method_name IS NOT NULL ORDER BY method_name")
            methods = [r["method_name"] for r in cur.fetchall()]
        if not methods:
            messagebox.showwarning("Внимание", "Список методик пуст")
            return

        dlg = MethodChoiceDialog(self, methods)
        self.wait_window(dlg)
        method = dlg.result
        if not method:
            return

        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")], title="Сохранить Markdown таблицу")
        if not path:
            return

        try:
            cur = self.registry.db._execute(
                "SELECT * FROM PARAMETER WHERE method_name=? ORDER BY long_code", (method,)
            )
            rows = cur.fetchall()
            if not rows:
                messagebox.showinfo("Экспорт в MD", f"Нет данных для методики '{method}'")
                return

            def md_escape(s: Any) -> str:
                t = str(s if s is not None else "")
                t = t.replace("|", "\\|").replace("\n", " ").replace("\r", " ")
                return t

            headers = ["Название", "Системная ед.", "Короткий код", "Длинный код"]
            lines = []
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join([":---:"] * len(headers)) + " |")

            for r in rows:
                labels = safe_json_loads(r["labels"], {})
                descr = safe_json_loads(r["description"], {})
                constr = safe_json_loads(r["constraints"], {})
                mn = constr.get("min", "")
                mx = constr.get("max", "")
                rng = f"{'' if mn is None else mn} - {'' if mx is None else mx}"

                row_vals = [
                    md_escape(labels.get("ru", "")),
                    md_escape(r["system_unit"]),
                    md_escape(r["short_code"] or ""),
                    md_escape(r["long_code"])
                ]
                lines.append("| " + " | ".join(row_vals) + " |")

            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")

            messagebox.showinfo("Экспорт в MD", f"Сохранено: {path}")
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать:\n{ex}")

    def _validate_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите параметр для проверки")
            return
        pid = sel[0]
        rep = self.registry.validate_parameter(pid)
        msg = []
        msg.append(f"OK: {'да' if rep['ok'] else 'нет'}")
        if rep["errors"]:
            msg.append("\nОшибки:")
            msg.extend([f"- {e}" for e in rep["errors"]])
        if rep["warnings"]:
            msg.append("\nПредупреждения:")
            msg.extend([f"- {w}" for w in rep["warnings"]])
        messagebox.showinfo("Отчёт валидации", "\n".join(msg))


class AllowedUnitsFrame(ttk.Frame):
    def __init__(self, master, db: Database, registry: ParameterRegistry):
        super().__init__(master)
        self.db = db
        self.registry = registry
        self.pid: Optional[str] = None
        self.vars: Dict[str, tk.BooleanVar] = {}
        self._build()

    def _build(self):
        ttk.Label(self, text="Разрешённые единицы").pack(anchor="w", padx=4, pady=4)
        self.units_frame = ttk.Frame(self)
        self.units_frame.pack(fill="x", padx=4, pady=4)

        btn_row = ttk.Frame(self)
        btn_row.pack(fill="x", padx=4, pady=4)
        ttk.Button(btn_row, text="Справочник единиц...", command=self._open_unit_manager).pack(side="left")
        self.save_btn = ttk.Button(btn_row, text="Сохранить", command=self._save)
        self.save_btn.pack(side="right")

    def _open_unit_manager(self):
        UnitManagerDialog(self, self.db).wait_window()
        # После закрытия — перечитать список
        if self.pid:
            self.load(self.pid)
        # Обновить список единиц в "Общее" и перезагрузить текущий параметр на вкладке "Общее"
        try:
            self.master.gen.refresh_units_choices()
            if self.pid:
                self.master.gen.load(self.pid)
        except Exception:
            pass
        self.event_generate("<<UnitsDictionaryChanged>>", when="tail")

    def load(self, pid: str):
        self.pid = pid
        for w in self.units_frame.winfo_children():
            w.destroy()
        self.vars.clear()
        cur = self.db._execute("SELECT code FROM UNIT ORDER BY code")
        all_units = [r["code"] for r in cur.fetchall()]
        allowed = set(self.registry.allowedUnits(pid))
        cols = 4
        r = 0
        c = 0
        for u in all_units:
            var = tk.BooleanVar(value=(u in allowed))
            cb = ttk.Checkbutton(self.units_frame, text=u, variable=var)
            cb.grid(row=r, column=c, sticky="w", padx=4, pady=2)
            self.vars[u] = var
            c += 1
            if c >= cols:
                c = 0
                r += 1

    def _save(self):
        if not self.pid:
            return
        allowed = [u for u, v in self.vars.items() if v.get()]
        sys_u = self.registry.systemUnit(self.pid)
        if sys_u not in allowed:
            if not messagebox.askyesno("Внимание", f"Системная единица {sys_u} не выбрана в allowedUnits.\nСохранить всё равно?"):
                return
        p = self.registry.getById(self.pid)
        param = {
            "longCode": p["long_code"],
            "quantityKind": p["quantity_kind"],
            "dataType": p["data_type"],
            "shape": p["shape"],
            "systemUnit": p["system_unit"],
            "method": p["method_name"] or "",
            "shortCode": p["short_code"] or "",
            "labels": safe_json_loads(p["labels"], {}),
            "description": safe_json_loads(p["description"], {}),
            "tags": safe_json_loads(p["tags"], []),
            "constraints": safe_json_loads(p["constraints"], {}),
            "allowedUnits": allowed,
        }
        try:
            self.registry.update_parameter(self.pid, param)
            messagebox.showinfo("OK", "Разрешённые единицы обновлены")
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{ex}")


class UnitManagerDialog(tk.Toplevel):
    def __init__(self, master, db: Database):
        super().__init__(master)
        self.db = db
        self.title("Справочник единиц")
        self.geometry("640x480")
        self.transient(master)
        self.grab_set()

        top = ttk.Frame(self)
        top.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree = ttk.Treeview(top, columns=("code","dim"), show="headings", height=16)
        self.tree.pack(fill="both", expand=True, side="left")
        for k, t, w in [
            ("code", "Код", 200),
            ("dim", "Размерность", 300),
        ]:
            self.tree.heading(k, text=t)
            self.tree.column(k, width=w, anchor="w")

        yscroll = ttk.Scrollbar(top, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=yscroll.set)
        yscroll.pack(side="right", fill="y")

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=8, pady=8)
        ttk.Button(btns, text="Добавить", command=self._add).pack(side="left")
        ttk.Button(btns, text="Изменить", command=self._edit).pack(side="left", padx=6)
        ttk.Button(btns, text="Удалить", command=self._delete).pack(side="left", padx=6)
        ttk.Button(btns, text="Закрыть", command=self.destroy).pack(side="right")

        self._refresh()

    def _refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        cur = self.db._execute("SELECT code, dimension FROM UNIT ORDER BY code")
        for r in cur.fetchall():
            self.tree.insert("", "end", iid=r["code"], values=(r["code"], r["dimension"] or ""))

    def _add(self):
        code = simpledialog.askstring("Новая единица", "Код единицы (уникально, напр., Pa):", parent=self)
        if not code:
            return
        code = code.strip()
        if not code:
            return
        cur = self.db._execute("SELECT 1 FROM UNIT WHERE code=?", (code,))
        if cur.fetchone():
            messagebox.showerror("Ошибка", f"Единица '{code}' уже существует")
            return
        dim = simpledialog.askstring("Новая единица", "Размерность (напр., pressure):", parent=self) or ""
        self.db._execute("INSERT INTO UNIT(code, dimension) VALUES (?, ?)", (code, dim.strip()))
        self._refresh()

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите единицу")
            return
        old_code = sel[0]
        cur = self.db._execute("SELECT code, dimension FROM UNIT WHERE code=?", (old_code,))
        row = cur.fetchone()
        if not row:
            return
        new_code = simpledialog.askstring("Правка единицы", "Код единицы (можно изменить):", initialvalue=row["code"], parent=self) or row["code"]
        new_code = new_code.strip()
        dim = simpledialog.askstring("Правка единицы", "Размерность:", initialvalue=row["dimension"] or "", parent=self) or ""
        try:
            self.db.rename_unit_with_dimension(old_code, new_code, dim.strip())
            self._refresh()
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{ex}")

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите единицу")
            return
        code = sel[0]
        if not messagebox.askyesno(
            "Подтверждение",
            f"Удалить единицу '{code}'?\n"
            f"Внимание: записи allowedUnits будут удалены (ON DELETE CASCADE). "
            f"Параметры с systemUnit='{code}' останутся со ссылкой на несуществующую единицу."
        ):
            return
        try:
            self.db._execute("DELETE FROM UNIT WHERE code=?", (code,))
            self._refresh()
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось удалить:\n{ex}")


class SegmentManagerDialog(tk.Toplevel):
    KIND_LABELS = [
        ("quantity", "Величина (quantity)"),
        ("medium", "Среда (medium)"),
        ("location", "Место (location)"),
        ("component", "Компонент (component)"),
        ("state", "Состояние (state)"),
        ("statistic", "Статистика (statistic)"),
        ("method", "Методика (method)"),
    ]
    def __init__(self, master, db: Database):
        super().__init__(master)
        self.db = db
        self.title("Справочник сегментов long code")
        self.geometry("760x520")
        self.transient(master)
        self.grab_set()

        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)
        ttk.Label(top, text="Словарь:").pack(side="left")
        self.kind_var = tk.StringVar(value="quantity")
        self.kind_combo = ttk.Combobox(top, textvariable=self.kind_var, values=[k for k, _ in self.KIND_LABELS], width=16, state="readonly")
        self.kind_combo.pack(side="left", padx=6)
        self.kind_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        mid = ttk.Frame(self)
        mid.pack(fill="both", expand=True, padx=8, pady=6)

        self.tree = ttk.Treeview(mid, columns=("value","label","notes"), show="headings", height=16)
        self.tree.pack(fill="both", expand=True, side="left")
        self.tree.heading("value", text="Значение (slug)")
        self.tree.heading("label", text="Метка")
        self.tree.heading("notes", text="Примечания")
        self.tree.column("value", width=220, anchor="w")
        self.tree.column("label", width=220, anchor="w")
        self.tree.column("notes", width=280, anchor="w")

        yscroll = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=yscroll.set)
        yscroll.pack(side="right", fill="y")

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=8, pady=6)
        ttk.Button(btns, text="Добавить", command=self._add).pack(side="left")
        ttk.Button(btns, text="Изменить", command=self._edit).pack(side="left", padx=6)
        ttk.Button(btns, text="Удалить", command=self._delete).pack(side="left", padx=6)
        ttk.Button(btns, text="Закрыть", command=self.destroy).pack(side="right")

        self._refresh()

    def _refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        kind = self.kind_var.get()
        for r in self.db.list_segments(kind):
            iid = f"{r['kind']}::{r['value']}"
            self.tree.insert("", "end", iid=iid, values=(r["value"], r["label"] or "", r["notes"] or ""))

    def _add(self):
        kind = self.kind_var.get()
        raw = simpledialog.askstring("Новый сегмент", "Значение (будет приведено к slug [a-z0-9-]):", parent=self)
        if not raw:
            return
        value = slugify(raw)
        if not value:
            messagebox.showerror("Ошибка", "Значение пустое после нормализации")
            return
        label = simpledialog.askstring("Новый сегмент", "Метка (опц.):", parent=self) or ""
        notes = simpledialog.askstring("Новый сегмент", "Примечания (опц.):", parent=self) or ""
        try:
            self.db.add_segment(kind, value, label, notes)
            self._refresh()
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось добавить:\n{ex}")

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите запись")
            return
        kind = self.kind_var.get()
        vals = self.tree.item(sel[0], "values")
        old_value, label0, notes0 = vals[0], vals[1], vals[2]
        raw = simpledialog.askstring("Правка сегмента", "Значение (slug):", initialvalue=old_value, parent=self)
        if not raw:
            return
        new_value = slugify(raw)
        label = simpledialog.askstring("Правка сегмента", "Метка (опц.):", initialvalue=label0, parent=self) or ""
        notes = simpledialog.askstring("Правка сегмента", "Примечания (опц.):", initialvalue=notes0, parent=self) or ""
        try:
            self.db.update_segment(kind, old_value, new_value, label, notes)
            self._refresh()
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{ex}")

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите запись")
            return
        kind = self.kind_var.get()
        vals = self.tree.item(sel[0], "values")
        value = vals[0]
        if not messagebox.askyesno("Подтверждение", f"Удалить '{value}' из словаря {kind}?"):
            return
        try:
            self.db.delete_segment(kind, value)
            self._refresh()
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось удалить:\n{ex}")


class DataDictManagerDialog(tk.Toplevel):
    KIND_LABELS = [
        ("quantity_kind", "Вид величины (quantityKind)"),
        ("data_type", "Тип данных (dataType)"),
        ("shape", "Форма (shape)"),
    ]
    def __init__(self, master, db: Database):
        super().__init__(master)
        self.db = db
        self.title("Справочник типа данных / видов / форм")
        self.geometry("760x520")
        self.transient(master)
        self.grab_set()

        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)
        ttk.Label(top, text="Справочник:").pack(side="left")
        self.kind_var = tk.StringVar(value="quantity_kind")
        self.kind_combo = ttk.Combobox(top, textvariable=self.kind_var, values=[k for k, _ in self.KIND_LABELS], width=20, state="readonly")
        self.kind_combo.pack(side="left", padx=6)
        self.kind_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        mid = ttk.Frame(self)
        mid.pack(fill="both", expand=True, padx=8, pady=6)

        self.tree = ttk.Treeview(mid, columns=("value","label","notes"), show="headings", height=16)
        self.tree.pack(fill="both", expand=True, side="left")
        self.tree.heading("value", text="Значение")
        self.tree.heading("label", text="Метка")
        self.tree.heading("notes", text="Примечания")
        self.tree.column("value", width=220, anchor="w")
        self.tree.column("label", width=220, anchor="w")
        self.tree.column("notes", width=280, anchor="w")

        yscroll = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=yscroll.set)
        yscroll.pack(side="right", fill="y")

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=8, pady=6)
        ttk.Button(btns, text="Добавить", command=self._add).pack(side="left")
        ttk.Button(btns, text="Изменить", command=self._edit).pack(side="left", padx=6)
        ttk.Button(btns, text="Удалить", command=self._delete).pack(side="left", padx=6)
        ttk.Button(btns, text="Закрыть", command=self.destroy).pack(side="right")

        self._refresh()

    def _refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        kind = self.kind_var.get()
        for r in self.db.list_data_dict(kind):
            iid = f"{r['kind']}::{r['value']}"
            self.tree.insert("", "end", iid=iid, values=(r["value"], r["label"] or "", r["notes"] or ""))

    def _add(self):
        kind = self.kind_var.get()
        value = simpledialog.askstring("Новое значение", "Значение:", parent=self)
        if not value:
            return
        value = value.strip()
        if not value:
            messagebox.showerror("Ошибка", "Значение пустое")
            return
        label = simpledialog.askstring("Новое значение", "Метка (опц.):", parent=self) or ""
        notes = simpledialog.askstring("Новое значение", "Примечания (опц.):", parent=self) or ""
        try:
            self.db.add_data_dict(kind, value, label, notes)
            self._refresh()
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось добавить:\n{ex}")

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите запись")
            return
        kind = self.kind_var.get()
        vals = self.tree.item(sel[0], "values")
        old_value, label0, notes0 = vals[0], vals[1], vals[2]
        value = simpledialog.askstring("Правка значения", "Значение:", initialvalue=old_value, parent=self) or old_value
        value = value.strip()
        label = simpledialog.askstring("Правка значения", "Метка (опц.):", initialvalue=label0, parent=self) or ""
        notes = simpledialog.askstring("Правка значения", "Примечания (опц.):", initialvalue=notes0, parent=self) or ""
        try:
            self.db.update_data_dict(kind, old_value, value, label, notes)
            self._refresh()
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{ex}")

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите запись")
            return
        kind = self.kind_var.get()
        vals = self.tree.item(sel[0], "values")
        value = vals[0]
        if not messagebox.askyesno("Подтверждение", f"Удалить '{value}' из справочника?"):
            return
        try:
            self.db.delete_data_dict(kind, value)
            self._refresh()
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось удалить:\n{ex}")


class GeneralParamFrame(ttk.Frame):
    def __init__(self, master, db: Database, registry: ParameterRegistry):
        super().__init__(master)
        self.db = db
        self.registry = registry
        self.pid: Optional[str] = None
        self.vars: Dict[str, tk.Variable] = {}
        self.cmb: Dict[str, ttk.Combobox] = {}
        self._in_seg_update = False
        self._build()

    def _rebuild_long(self, *args):
        if self._in_seg_update:
            return
        parts = []
        # Order of segments for assembly
        for key in ("seg_quantity", "seg_medium", "seg_location", "seg_component", "seg_state", "seg_statistic", "seg_method", "seg_context"):
            raw = self.vars[key].get().strip()
            if key == "seg_context":
                # context is free text; split by '.' and slugify each piece
                ctx = raw.strip()
                if ctx:
                    ctx_parts = [slugify(p) for p in ctx.split(".") if slugify(p)]
                    if ctx_parts:
                        parts.extend(ctx_parts)
                continue
            slug = slugify(raw)
            if slug:
                parts.append(slug)
        long_code = ".".join(parts)
        self.vars["long"].set(long_code)

    def _parse_long_to_segments(self, long_code: str):
        self._in_seg_update = True
        try:
            for key in ("seg_quantity", "seg_medium", "seg_location", "seg_component", "seg_state", "seg_statistic", "seg_method", "seg_context"):
                self.vars[key].set("")
            segs = (long_code or "").split(".") if long_code else []
            if not segs:
                return
            if len(segs) >= 1:
                self.vars["seg_quantity"].set(segs[0])
            if len(segs) >= 2:
                self.vars["seg_medium"].set(segs[1])
            rest = segs[2:]

            # словари из БД
            states = set(self.db.list_segment_values("state"))
            statistics = set(self.db.list_segment_values("statistic"))
            locations = set(self.db.list_segment_values("location"))
            components = set(self.db.list_segment_values("component"))
            methods = set(self.db.list_segment_values("method"))

            state = next((s for s in rest if s in states), "")
            stat = next((s for s in rest if s in statistics), "")
            loc = next((s for s in rest if (s in locations or s.startswith(("node-", "section-", "station-")))), "")
            comp = next((s for s in rest if s in components), "")
            meth = next((s for s in rest if s in methods), "")
            used = set(x for x in (state, stat, loc, comp, meth) if x)
            context_parts = [s for s in rest if s not in used]
            context = ".".join(context_parts) if context_parts else ""

            if loc:
                self.vars["seg_location"].set(loc)
            if comp:
                self.vars["seg_component"].set(comp)
            if state:
                self.vars["seg_state"].set(state)
            if stat:
                self.vars["seg_statistic"].set(stat)
            if meth:
                self.vars["seg_method"].set(meth)
            if context:
                self.vars["seg_context"].set(context)
        finally:
            self._in_seg_update = False
            self._rebuild_long()

    def _refresh_segment_choices(self):
        self.cmb["seg_quantity"]["values"] = [""] + self.db.list_segment_values("quantity")
        self.cmb["seg_medium"]["values"] = [""] + self.db.list_segment_values("medium")
        self.cmb["seg_location"]["values"] = [""] + self.db.list_segment_values("location")
        self.cmb["seg_component"]["values"] = [""] + self.db.list_segment_values("component")
        self.cmb["seg_state"]["values"] = [""] + self.db.list_segment_values("state")
        self.cmb["seg_statistic"]["values"] = [""] + self.db.list_segment_values("statistic")
        self.cmb["seg_method"]["values"] = [""] + self.db.list_segment_values("method")

    def refresh_units_choices(self):
        cur = self.db._execute("SELECT code FROM UNIT ORDER BY code")
        units = [r["code"] for r in cur.fetchall()]
        if "systemUnit" in self.cmb:
            self.cmb["systemUnit"]["values"] = units

    def refresh_data_dict_choices(self):
        qk = self.db.list_data_dict_values("quantity_kind")
        dt = self.db.list_data_dict_values("data_type")
        sh = self.db.list_data_dict_values("shape")
        if "quantity" in self.cmb:
            self.cmb["quantity"]["values"] = qk
        if "dataType" in self.cmb:
            self.cmb["dataType"]["values"] = dt
        if "shape" in self.cmb:
            self.cmb["shape"]["values"] = sh

    def _open_segments_manager(self):
        SegmentManagerDialog(self, self.db).wait_window()
        self._refresh_segment_choices()

    def _open_data_manager(self):
        DataDictManagerDialog(self, self.db).wait_window()
        self.refresh_data_dict_choices()

    def _build(self):
        self.vars["id"] = tk.StringVar()
        self.vars["long"] = tk.StringVar()

        # Сегменты длинного кода
        self.vars["seg_quantity"] = tk.StringVar()
        self.vars["seg_medium"] = tk.StringVar()
        self.vars["seg_location"] = tk.StringVar()
        self.vars["seg_component"] = tk.StringVar()
        self.vars["seg_state"] = tk.StringVar()
        self.vars["seg_statistic"] = tk.StringVar()
        self.vars["seg_method"] = tk.StringVar()
        self.vars["seg_context"] = tk.StringVar()

        self.vars["shortCode"] = tk.StringVar()

        self.vars["quantity"] = tk.StringVar()
        self.vars["dataType"] = tk.StringVar(value="float64")
        self.vars["shape"] = tk.StringVar(value="scalar")
        self.vars["systemUnit"] = tk.StringVar(value="K")
        self.vars["label_ru"] = tk.StringVar()
        self.vars["desc_ru"] = tk.StringVar()
        self.vars["tags"] = tk.StringVar()
        self.vars["cmin"] = tk.StringVar()
        self.vars["cmax"] = tk.StringVar()

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=6, pady=6)

        row = 0
        ttk.Label(frm, text="PID:").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.vars["id"], state="readonly", width=20).grid(row=row, column=1, sticky="w")
        row += 1

        seg_box = ttk.Labelframe(frm, text="Сегменты длинного кода (автосборка)")
        seg_box.grid(row=row, column=0, columnspan=4, sticky="we", pady=(0, 6))
        row += 1

        # строка 1: величина, среда
        ttk.Label(seg_box, text="Величина:").grid(row=0, column=0, sticky="w")
        cbq = ttk.Combobox(seg_box, textvariable=self.vars["seg_quantity"], values=[""] + self.db.list_segment_values("quantity"), width=20)
        cbq.grid(row=0, column=1, sticky="w", padx=4, pady=2); self.cmb["seg_quantity"] = cbq
        ttk.Label(seg_box, text="Среда:").grid(row=0, column=2, sticky="e")
        cbm = ttk.Combobox(seg_box, textvariable=self.vars["seg_medium"], values=[""] + self.db.list_segment_values("medium"), width=20)
        cbm.grid(row=0, column=3, sticky="w", padx=4, pady=2); self.cmb["seg_medium"] = cbm

        # строка 2: место, компонент
        ttk.Label(seg_box, text="Место:").grid(row=1, column=0, sticky="w")
        cbl = ttk.Combobox(seg_box, textvariable=self.vars["seg_location"], values=[""] + self.db.list_segment_values("location"), width=20)
        cbl.grid(row=1, column=1, sticky="w", padx=4, pady=2); self.cmb["seg_location"] = cbl
        ttk.Label(seg_box, text="Компонент:").grid(row=1, column=2, sticky="e")
        cbc = ttk.Combobox(seg_box, textvariable=self.vars["seg_component"], values=[""] + self.db.list_segment_values("component"), width=20)
        cbc.grid(row=1, column=3, sticky="w", padx=4, pady=2); self.cmb["seg_component"] = cbc

        # строка 3: состояние, статистика
        ttk.Label(seg_box, text="Состояние:").grid(row=2, column=0, sticky="w")
        cbs = ttk.Combobox(seg_box, textvariable=self.vars["seg_state"], values=[""] + self.db.list_segment_values("state"), width=20)
        cbs.grid(row=2, column=1, sticky="w", padx=4, pady=2); self.cmb["seg_state"] = cbs
        ttk.Label(seg_box, text="Статистика:").grid(row=2, column=2, sticky="e")
        cbst = ttk.Combobox(seg_box, textvariable=self.vars["seg_statistic"], values=[""] + self.db.list_segment_values("statistic"), width=20)
        cbst.grid(row=2, column=3, sticky="w", padx=4, pady=2); self.cmb["seg_statistic"] = cbst

        # строка 4: методика
        ttk.Label(seg_box, text="Методика:").grid(row=3, column=0, sticky="w")
        cbmth = ttk.Combobox(seg_box, textvariable=self.vars["seg_method"], values=[""] + self.db.list_segment_values("method"), width=20)
        cbmth.grid(row=3, column=1, sticky="w", padx=4, pady=2); self.cmb["seg_method"] = cbmth

        # строка 5: контекст
        ttk.Label(seg_box, text="Контекст:").grid(row=4, column=0, sticky="w")
        ttk.Entry(seg_box, textvariable=self.vars["seg_context"], width=50).grid(row=4, column=1, columnspan=3, sticky="we", padx=4, pady=2)
        seg_box.columnconfigure(1, weight=1)
        seg_box.columnconfigure(3, weight=1)

        # кнопка словарей сегментов
        ttk.Button(seg_box, text="Справочник сегментов...", command=self._open_segments_manager).grid(row=5, column=0, columnspan=4, sticky="w", padx=4, pady=(4, 2))

        for key in ("seg_quantity", "seg_medium", "seg_location", "seg_component", "seg_state", "seg_statistic", "seg_method", "seg_context"):
            self.vars[key].trace_add("write", self._rebuild_long)

        ttk.Label(frm, text="Длинный код:").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.vars["long"], width=60, state="readonly").grid(row=row, column=1, columnspan=3, sticky="we", pady=2)
        row += 1

        # короткий код
        ttk.Label(frm, text="Короткий код:").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.vars["shortCode"], width=32).grid(row=row, column=1, sticky="w")
        row += 1

        ttk.Label(frm, text="Вид величины:").grid(row=row, column=0, sticky="w")
        cbqk = ttk.Combobox(frm, textvariable=self.vars["quantity"], values=self.db.list_data_dict_values("quantity_kind"), width=28)
        cbqk.grid(row=row, column=1, sticky="w"); self.cmb["quantity"] = cbqk
        ttk.Label(frm, text="Тип данных:").grid(row=row, column=2, sticky="e")
        cbdt = ttk.Combobox(frm, textvariable=self.vars["dataType"], values=self.db.list_data_dict_values("data_type"), width=12)
        cbdt.grid(row=row, column=3, sticky="w"); self.cmb["dataType"] = cbdt
        row += 1

        ttk.Label(frm, text="Форма:").grid(row=row, column=0, sticky="w")
        cbsh = ttk.Combobox(frm, textvariable=self.vars["shape"], values=self.db.list_data_dict_values("shape"), width=12)
        cbsh.grid(row=row, column=1, sticky="w"); self.cmb["shape"] = cbsh
        ttk.Label(frm, text="Системная единица:").grid(row=row, column=2, sticky="e")
        cur = self.db._execute("SELECT code FROM UNIT ORDER BY code")
        units = [r["code"] for r in cur.fetchall()]
        cbsu = ttk.Combobox(frm, textvariable=self.vars["systemUnit"], values=units, width=12)
        cbsu.grid(row=row, column=3, sticky="w"); self.cmb["systemUnit"] = cbsu
        row += 1

        # Кнопка управления словарями видов/типов/форм
        ttk.Button(frm, text="Справочник типа данных...", command=self._open_data_manager).grid(row=row, column=0, columnspan=4, sticky="w", pady=(2, 8))
        row += 1

        ttk.Label(frm, text="Название:").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.vars["label_ru"], width=60).grid(row=row, column=1, columnspan=3, sticky="we")
        row += 1

        ttk.Label(frm, text="Описание:").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.vars["desc_ru"], width=60).grid(row=row, column=1, columnspan=3, sticky="we")
        row += 1

        ttk.Label(frm, text="Теги (через запятую):").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.vars["tags"], width=60).grid(row=row, column=1, columnspan=3, sticky="we")
        row += 1

        ttk.Label(frm, text="Ограничения, мин:").grid(row=row, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.vars["cmin"], width=10).grid(row=row, column=1, sticky="w")
        ttk.Label(frm, text="макс:").grid(row=row, column=2, sticky="e")
        ttk.Entry(frm, textvariable=self.vars["cmax"], width=10).grid(row=row, column=3, sticky="w")
        row += 1

        frm.columnconfigure(1, weight=1)
        frm.columnconfigure(3, weight=1)

        self.save_btn = ttk.Button(self, text="Сохранить", command=self._save)
        self.save_btn.pack(anchor="e", padx=6, pady=6)

    def load(self, pid: Optional[str]):
        self.pid = pid
        if not pid:
            for v in self.vars.values():
                if isinstance(v, tk.BooleanVar):
                    v.set(False)
                else:
                    v.set("")
            return
        row = self.registry.getById(pid)
        if not row:
            return
        self.vars["id"].set(row["id"])
        self.vars["long"].set(row["long_code"])
        self._parse_long_to_segments(row["long_code"])

        self.vars["shortCode"].set(row["short_code"] or "")

        self.vars["quantity"].set(row["quantity_kind"])
        self.vars["dataType"].set(row["data_type"])
        self.vars["shape"].set(row["shape"])
        self.vars["systemUnit"].set(row["system_unit"])
        labels = safe_json_loads(row["labels"], {})
        self.vars["label_ru"].set(labels.get("ru", ""))
        desc = safe_json_loads(row["description"], {})
        self.vars["desc_ru"].set(desc.get("ru", ""))
        tags = safe_json_loads(row["tags"], [])
        self.vars["tags"].set(", ".join(tags))
        constraints = safe_json_loads(row["constraints"], {})
        self.vars["cmin"].set("" if "min" not in constraints else str(constraints["min"]))
        self.vars["cmax"].set("" if "max" not in constraints else str(constraints["max"]))

    def _save(self):
        if not self.pid:
            return
        try:
            long_code = self.vars["long"].get().strip().lower()
            quantity = self.vars["quantity"].get().strip()
            dataType = self.vars["dataType"].get().strip()
            shape = self.vars["shape"].get().strip()
            systemUnit = self.vars["systemUnit"].get().strip()
            method = self.vars["seg_method"].get().strip()
            short_code = self.vars["shortCode"].get().strip()
            labels = {"ru": self.vars["label_ru"].get().strip()}
            desc = {"ru": self.vars["desc_ru"].get().strip()}
            tags = [t.strip() for t in self.vars["tags"].get().split(",") if t.strip()]
            cmin = self.vars["cmin"].get().strip()
            cmax = self.vars["cmax"].get().strip()
            constraints = {}
            if cmin != "":
                constraints["min"] = float(cmin)
            if cmax != "":
                constraints["max"] = float(cmax)

            # Валидации
            errs, _ = self.registry.validate_long_code(long_code)
            if short_code and not SHORT_CODE_RE.match(short_code):
                errs.append("shortCode должен начинаться с буквы и содержать до 32 символов [A-Za-z0-9_]")
            if short_code and method and not self.registry.is_short_code_unique(method, short_code, exclude_pid=self.pid):
                errs.append(f"shortCode '{short_code}' уже используется в методике '{method}'")
            if errs:
                messagebox.showerror("Ошибка", "Найдены ошибки:\n- " + "\n- ".join(errs))
                return

            allowed = self.registry.allowedUnits(self.pid)

            param = {
                "longCode": long_code,
                "quantityKind": quantity,
                "dataType": dataType,
                "shape": shape,
                "systemUnit": systemUnit,
                "method": method,
                "shortCode": short_code,
                "labels": labels,
                "description": desc,
                "tags": tags,
                "constraints": constraints,
                "allowedUnits": allowed,
            }
            self.registry.update_parameter(self.pid, param)
            messagebox.showinfo("OK", "Параметр сохранён")
            # Сообщить приложению об успешном сохранении (обновить список слева и вкладки)
            self.event_generate("<<ParameterSaved>>", when="tail")
        except Exception as ex:
            messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{ex}")


class ValidationFrame(ttk.Frame):
    def __init__(self, master, registry: ParameterRegistry):
        super().__init__(master)
        self.registry = registry
        self.pid: Optional[str] = None
        self._build()

    def _build(self):
        self.txt = tk.Text(self, height=12, wrap="word")
        self.txt.pack(fill="both", expand=True, padx=4, pady=4)
        self.btn = ttk.Button(self, text="Прогнать валидацию", command=self._run)
        self.btn.pack(anchor="e", padx=4, pady=4)

    def load(self, pid: str):
        self.pid = pid
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", "Нажмите 'Прогнать валидацию'")

    def _run(self):
        if not self.pid:
            return
        rep = self.registry.validate_parameter(self.pid)
        self.txt.delete("1.0", "end")
        self.txt.insert("end", f"OK: {'да' if rep['ok'] else 'нет'}\n")
        if rep["errors"]:
            self.txt.insert("end", "\nОшибки:\n")
            for e in rep["errors"]:
                self.txt.insert("end", f"- {e}\n")
        if rep["warnings"]:
            self.txt.insert("end", "\nПредупреждения:\n")
            for w in rep["warnings"]:
                self.txt.insert("end", f"- {w}\n")


class ParameterDetail(ttk.Notebook):
    def __init__(self, master, db: Database, registry: ParameterRegistry):
        super().__init__(master)
        self.db = db
        self.registry = registry

        self.gen = GeneralParamFrame(self, db, registry)
        self.add(self.gen, text="Общее")

        self.allowed = AllowedUnitsFrame(self, db, registry)
        self.add(self.allowed, text="Единицы")

        self.validation = ValidationFrame(self, registry)
        self.add(self.validation, text="Валидация")

    def load(self, pid: Optional[str]):
        self.gen.load(pid)
        if pid:
            self.allowed.load(pid)
            self.validation.load(pid)


# ------------------------- Main App -------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1280x800")

        self.db = Database()
        self.reg = ParameterRegistry(self.db)

        self._help_win = None
        self._build_ui()

    def _build_ui(self):
        # Menu bar
        menubar = tk.Menu(self)
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Инструкция (F1)", command=self.show_help)
        helpmenu.add_separator()
        helpmenu.add_command(label="О программе", command=self.show_about)
        self.config(menu=menubar)
        menubar.add_cascade(label="Справка", menu=helpmenu)

        paned = ttk.Panedwindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)

        left = ttk.Frame(paned)
        paned.add(left, weight=1)

        right = ttk.Frame(paned)
        paned.add(right, weight=3)

        # Left: list
        self.list_frame = ParameterListFrame(left, self.reg, self._on_select_param)
        self.list_frame.pack(fill="both", expand=True)

        # Right: details
        self.detail = ParameterDetail(right, self.db, self.reg)
        self.detail.pack(fill="both", expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="Готово — нажмите F1 для Справки")
        status = ttk.Label(self, textvariable=self.status_var, anchor="w")
        status.pack(fill="x", side="bottom")

        # Bindings
        self.bind("<F1>", self.show_help)
        self.bind("<<ParameterSaved>>", self._on_param_saved)
        self.bind("<<UnitsDictionaryChanged>>", self._on_units_changed)

    def _on_units_changed(self, event=None):
        # Обновить список единиц в "Общее"
        try:
            self.detail.gen.refresh_units_choices()
        except Exception:
            pass
        # Перезагрузить текущий параметр (на всякий случай)
        sel = self.list_frame.tree.selection()
        if sel:
            pid = sel[0]
            self.detail.gen.load(pid)

    def _on_param_saved(self, event=None):
        # Обновить список слева и перезагрузить детали текущего параметра
        sel = self.list_frame.tree.selection()
        pid = sel[0] if sel else None
        self.list_frame.refresh()
        if pid:
            try:
                self.list_frame.tree.selection_set(pid)
            except Exception:
                pass
            self.detail.load(pid)

    def _on_select_param(self, pid: Optional[str]):
        self.detail.load(pid)
        if pid:
            p = self.reg.getById(pid)
            if p:
                self.status_var.set(f"Выбран: {p['id']} — {p['long_code']}")
        else:
            self.status_var.set("Нет выбора")

    def show_help(self, event=None):
        if self._help_win and self._help_win.winfo_exists():
            self._help_win.lift()
            self._help_win.focus_set()
            return

        win = tk.Toplevel(self)
        win.title("Справка — Инструкция")
        win.geometry("960x720")
        win.transient(self)
        self._help_win = win

        def on_close():
            if self._help_win and self._help_win.winfo_exists():
                self._help_win.destroy()
            self._help_win = None

        win.protocol("WM_DELETE_WINDOW", on_close)

        toolbar = ttk.Frame(win)
        toolbar.pack(fill="x", padx=6, pady=6)
        ttk.Label(toolbar, text="Найти:").pack(side="left")
        search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=search_var, width=32)
        search_entry.pack(side="left", padx=4)
        btn_find = ttk.Button(toolbar, text="Найти далее")
        btn_find.pack(side="left")
        ttk.Label(toolbar, text="  (Enter — найти)").pack(side="left")

        frame = ttk.Frame(win)
        frame.pack(fill="both", expand=True, padx=6, pady=6)
        yscroll = ttk.Scrollbar(frame, orient="vertical")
        text = tk.Text(frame, wrap="word", yscrollcommand=yscroll.set)
        yscroll.config(command=text.yview)
        yscroll.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)

        text.insert("1.0", HELP_TEXT)
        text.config(state="disabled")

        def do_search(event=None):
            pat = search_var.get().strip()
            if not pat:
                return
            text.config(state="normal")
            text.tag_remove("found", "1.0", "end")
            start = text.index(tk.INSERT)
            idx = text.search(pat, start, nocase=True, stopindex="end")
            if not idx:
                idx = text.search(pat, "1.0", nocase=True, stopindex="end")
                if not idx:
                    text.config(state="disabled")
                    return
            end = f"{idx}+{len(pat)}c"
            text.tag_add("found", idx, end)
            text.tag_config("found", background="#ffe58a")
            text.mark_set(tk.INSERT, end)
            text.see(idx)
            text.config(state="disabled")

        btn_find.config(command=do_search)
        search_entry.bind("<Return>", do_search)

    def show_about(self):
        messagebox.showinfo("О программе", f"{APP_NAME}\nВерсия: {APP_VERSION}\n\nЛокальный реестр параметров с единицами и короткими кодами.\nSQLite: registry.db\nСправка: F1")


if __name__ == "__main__":
    App().mainloop()