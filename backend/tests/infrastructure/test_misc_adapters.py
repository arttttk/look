import logging
from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.infrastructure.clock import SystemClock
from app.infrastructure.db.base import Base, UTCDateTime, make_engine
from app.infrastructure.senders import ConsoleSender


class TestSystemClock:
    def test_now_is_timezone_aware_utc(self):
        # Arrange: подготовка не требуется
        # Act
        now = SystemClock().now()

        # Assert
        assert now.tzinfo is not None and now.utcoffset() == timedelta(0)

    def test_now_is_close_to_the_real_time(self):
        # Arrange
        before = datetime.now(UTC)

        # Act
        now = SystemClock().now()

        # Assert
        assert before <= now <= datetime.now(UTC)


class TestConsoleSender:
    def test_the_code_is_written_to_the_log(self, caplog):
        # Arrange
        sender = ConsoleSender()

        # Act
        with caplog.at_level(logging.WARNING, logger="look.auth"):
            sender.send("phone", "+79991234567", "123456")

        # Assert
        assert "+79991234567" in caplog.text and "123456" in caplog.text


class TestUtcDateTime:
    @pytest.fixture()
    def column(self):
        return UTCDateTime()

    def test_an_aware_time_is_stored_in_utc(self, column):
        # Arrange
        moscow = datetime(2026, 10, 20, 15, 0, tzinfo=timezone(timedelta(hours=3)))

        # Act
        stored = column.process_bind_param(moscow, None)

        # Assert
        assert stored == datetime(2026, 10, 20, 12, 0, tzinfo=UTC) and stored.utcoffset() == timedelta(0)

    def test_a_naive_time_is_refused(self, column):
        # Arrange
        naive = datetime(2026, 10, 20, 12, 0)

        # Act / Assert
        with pytest.raises(ValueError, match="часовым поясом"):
            column.process_bind_param(naive, None)

    def test_a_time_read_back_from_sqlite_becomes_utc_aware(self, column):
        # Arrange: SQLite отдаёт время без пояса
        raw = datetime(2026, 10, 20, 12, 0)

        # Act
        loaded = column.process_result_value(raw, None)

        # Assert
        assert loaded == datetime(2026, 10, 20, 12, 0, tzinfo=UTC)

    def test_none_stays_none_both_ways(self, column):
        # Arrange: состояние задают фикстуры (column)
        # Act / Assert
        assert column.process_bind_param(None, None) is None
        assert column.process_result_value(None, None) is None


class TestEngine:
    @pytest.fixture()
    def disposable(self):
        engines = []
        yield engines.append
        for engine in engines:
            engine.dispose()

    def test_an_in_memory_database_is_shared_between_sessions(self, disposable):
        # Arrange
        engine = make_engine("sqlite://")
        disposable(engine)
        Base.metadata.create_all(engine)
        insert = (
            "insert into products (id, title, brand, price, category, color, styles, department, "
            "warmth, weatherproof, url) values ('p', 't', 'b', 1, 'top', 'black', '[]', 'unisex', 1, 1, 'u')"
        )

        # Act
        with engine.connect() as first:
            first.execute(text(insert))
            first.commit()
        with engine.connect() as second:
            count = second.execute(text("select count(*) from products")).scalar()

        # Assert
        assert count == 1

    def test_a_file_database_is_created_on_demand(self, tmp_path, disposable):
        # Arrange
        path = tmp_path / "look.db"

        # Act
        engine = make_engine(f"sqlite:///{path}")
        disposable(engine)
        Base.metadata.create_all(engine)

        # Assert
        assert path.exists()
