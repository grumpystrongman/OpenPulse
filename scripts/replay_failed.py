from __future__ import annotations

from datetime import datetime, timezone

from openpulse_data.clickhouse import execute, query
from openpulse_data.kafka import get_producer
from openpulse_data.settings import settings


def main(limit: int = 100) -> None:
    producer = get_producer()
    rows = query(
        f"""
        SELECT failed_id, envelope_json
        FROM openpulse.failed_record_queue
        WHERE replay_status = 'pending'
        ORDER BY failed_at ASC
        LIMIT {limit}
        """
    )
    for row in rows:
        producer.produce(settings.kafka_raw_topic, value=row["envelope_json"].encode("utf-8"))
        execute(
            f"""
            ALTER TABLE openpulse.failed_record_queue
            UPDATE replay_status = 'replayed', replayed_at = toDateTime64('{datetime.now(tz=timezone.utc).isoformat()}', 3, 'UTC')
            WHERE failed_id = '{row['failed_id']}'
            """
        )
    producer.flush(10)
    print(f"Replayed {len(rows)} failed records")


if __name__ == "__main__":
    main()
