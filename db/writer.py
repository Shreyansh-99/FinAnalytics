# db/writer.py
import threading
import time
import logging
from typing import List, Tuple, Dict
from db.connection import get_connection  # your existing helper

logger = logging.getLogger("finanalytics.db.writer")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(ch)

BUFFER_SIZE = 500
FLUSH_INTERVAL_SECONDS = 2.0

class EventWriter:
    def __init__(self):
        # DB connection and cursor (recreated on error)
        self.conn = get_connection()
        self.cur = self.conn.cursor()

        # Buffer and synchronization
        self.buffer: List[Tuple] = []
        self.cond = threading.Condition()
        self._stop_event = threading.Event()
        self._drain_event = threading.Event()

        # Start background flusher
        self._flusher_thread = threading.Thread(target=self._flusher_loop, name="EventWriterFlusher", daemon=True)
        self._flusher_thread.start()
        logger.info("EventWriter started (flush interval=%ss, buffer_size=%d)", FLUSH_INTERVAL_SECONDS, BUFFER_SIZE)

    def log_event(self, event: Dict):
        """
        Append event to buffer. Expected keys: time, payment_id, order_id, user, amount, method, status, reason, retry
        """
        row = (
            event.get("event_key"),
            event.get("time"),
            event.get("payment_id"),
            event.get("order_id"),
            event.get("user"),
            None,  # merchant_id placeholder
            event.get("amount"),
            "INR",
            event.get("method"),
            event.get("provider", event.get("method")),
            event.get("status"),
            event.get("reason"),
            event.get("city"),
            event.get("device"),
            event.get("retry", False),
            None
        )

        with self.cond:
            self.buffer.append(row)
            if len(self.buffer) >= BUFFER_SIZE:
                # wake flusher immediately
                self.cond.notify_all()

    def _flusher_loop(self):
        while not self._stop_event.is_set():
            with self.cond:
                # wait for notify or timeout
                self.cond.wait(timeout=FLUSH_INTERVAL_SECONDS)
                if not self.buffer:
                    continue
                rows_to_flush = self.buffer
                self.buffer = []

            try:
                self._flush_rows(rows_to_flush)
            except Exception as e:
                logger.exception("Flush failed: %s", e)
                # requeue on failure
                with self.cond:
                    self.buffer = rows_to_flush + self.buffer
                time.sleep(1)

            # signal any waiting flush() caller if buffer is empty
            with self.cond:
                if not self.buffer:
                    # set then clear so waiters can observe
                    self._drain_event.set()
                    self._drain_event.clear()

        # final flush on stop
        with self.cond:
            remaining = self.buffer
            self.buffer = []
        if remaining:
            try:
                self._flush_rows(remaining)
            except Exception:
                logger.exception("Final flush failed during shutdown; rows may be lost")
        logger.info("Flusher thread exiting")

    def _flush_rows(self, rows: List[Tuple]):
        if not rows:
            return
        try:
            self.cur.executemany("""
                INSERT INTO raw.payment_events (
                    event_key, event_time, payment_id, order_id, user_id, merchant_id,
                    amount, currency, payment_method, provider,
                    status, failure_reason, city, device, is_retry, latency_ms
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (event_key) DO NOTHING
            """, rows)
            self.conn.commit()
            logger.info("Flushed %d events to raw.payment_events", len(rows))
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception:
                pass
            logger.warning("DB write failed (%s). Reconnecting.", e)
            # close and recreate connection for next attempts
            try:
                self.cur.close()
            except Exception:
                pass
            try:
                self.conn.close()
            except Exception:
                pass
            try:
                self.conn = get_connection()
                self.cur = self.conn.cursor()
                logger.info("Reconnected to DB after failure")
            except Exception:
                logger.exception("Reconnection failed")
            raise

    def flush(self, timeout: float = 5.0) -> bool:
        """
        Force immediate flush and wait until buffer drained or timeout.
        Returns True if drained, False if timed out.
        """
        with self.cond:
            if not self.buffer:
                return True
            self.cond.notify_all()

        drained = self._drain_event.wait(timeout=timeout)
        if not drained:
            logger.warning("flush() timed out after %.2fs; buffer may still contain rows", timeout)
        return drained

    def stop(self, wait: float = 5.0):
        """
        Graceful shutdown: stop flusher, flush remaining rows synchronously, close DB.
        """
        logger.info("Stopping EventWriter")
        self._stop_event.set()
        with self.cond:
            self.cond.notify_all()
        self._flusher_thread.join(timeout=wait)

        # final synchronous flush
        with self.cond:
            remaining = self.buffer
            self.buffer = []
        if remaining:
            try:
                self._flush_rows(remaining)
            except Exception:
                logger.exception("Final flush failed during shutdown; rows may be lost")

        try:
            self.cur.close()
        except Exception:
            pass
        try:
            self.conn.close()
        except Exception:
            pass
        logger.info("EventWriter stopped")
