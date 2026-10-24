import logging
import os
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from run_ingest import main as run_rss_ingest
from run_chunking import main as run_chunking
from build_bm25_index import main as run_build_index


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("scheduler")


def refresh_pipeline():
    """Полный цикл: RSS → чистка → чанки → индекс."""
    log.info("=== Старт обновления данных ===")
    try:
        run_rss_ingest()
        run_chunking()
        run_build_index()
        log.info("=== Обновление завершено ===")
    except Exception as e:
        log.exception(f"Ошибка в пайплайне: {e}")


def start_scheduler(interval_minutes: int = 60):
    """
    Запускает бесконечный планировщик.
    :param interval_minutes: как часто обновлять (по умолчанию — каждый час)
    """
    scheduler = BlockingScheduler(timezone="Europe/Moscow")

    scheduler.add_job(
        refresh_pipeline,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="refresh_rss",
        name=f"RSS refresh every {interval_minutes} min",
        max_instances=1,          # не запускать параллельные копии
        coalesce=True,            # если пропустили — выполнить один раз
        misfire_grace_time=300,   # 5 минут допустимо опоздать
    )

    log.info(f"Планировщик запущен: обновление каждые {interval_minutes} мин.")
    log.info("Ctrl+C — остановить.")

    # Первый прогон сразу при старте (не ждать час)
    refresh_pipeline()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Планировщик остановлен.")


if __name__ == "__main__":
    interval = int(os.getenv("REFRESH_INTERVAL_MINUTES", "60"))
    start_scheduler(interval_minutes=interval)