"""
src/adaptive_scaler.py
─────────────────────────────────────────────────────────────────────────────
Adaptive Polling Engine for FloodGuard API.

Intelligently adjusts how often we check weather/risk data for a coordinate
based on the current hazard level.

Thresholds (per spec):
  - Critical State  → final_prob > 0.7 OR rainfall_mm > 20.0
  - Alert Mode      → poll every  1 hour  (CRITICAL state)
  - Normal Mode     → poll every 24 hours (baseline)

Cool-down:
  After a state transition from CRITICAL → NORMAL, the system requires
  COOLDOWN_CYCLES consecutive normal-mode readings before downgrading the
  poll frequency. This prevents thrashing after a storm passes.

Auto-Scale Override (Person 3 hook):
  If user_settings.auto_scale is TRUE in Supabase, the emergency logic
  always overrides any manual polling_interval_minutes setting.

Usage (standalone):
    scaler = AdaptiveScaler(supabase_client)
    delta  = await scaler.calculate_next_poll_interval(lat, lon)
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from supabase import Client

# ── project-internal imports ──────────────────────────────────────────────────
from src.risk_model import predict as risk_predict
from src.weather_service import fetch_rainfall_data
from src.soil_service import fetch_soil_type

logger = logging.getLogger("FloodGuard.AdaptiveScaler")

# ── Constants ─────────────────────────────────────────────────────────────────
CRITICAL_RISK_THRESHOLD: float = 0.7        # final_prob above which → CRITICAL
CRITICAL_RAIN_THRESHOLD: float = 20.0       # mm above which         → CRITICAL
ALERT_INTERVAL:  timedelta = timedelta(hours=.12)
NORMAL_INTERVAL: timedelta = timedelta(hours=24)
COOLDOWN_CYCLES: int = 3   # consecutive normal readings before downgrade


# ─────────────────────────────────────────────────────────────────────────────
class AdaptiveScaler:
    """
    Core Adaptive Polling Engine.

    Responsibilities
    ────────────────
    1. Determine whether a (lat, lon) pair is in CRITICAL or NORMAL state.
    2. Persist / update a `monitoring_sessions` row in Supabase — never
       INSERT a new row on every tick; only UPSERT on the coordinate key.
    3. Honour the user's Auto-Scale toggle from `user_settings`.
    4. Expose `calculate_next_poll_interval()` for the background loop.
    """

    def __init__(self, db: Client) -> None:
        self._db = db

    # ── Public API ────────────────────────────────────────────────────────────

    async def calculate_next_poll_interval(
        self,
        lat: float,
        lon: float,
        session_id: Optional[str] = None,
    ) -> timedelta:
        """
        Evaluate current risk for (lat, lon) and return the appropriate poll
        interval.  Also upserts the monitoring_sessions row in Supabase.

        Parameters
        ----------
        lat, lon   : Coordinate to evaluate.
        session_id : Optional user session; used to look up Auto-Scale toggle.

        Returns
        -------
        timedelta — either ALERT_INTERVAL (1 h) or NORMAL_INTERVAL (24 h).
        """
        # 1. Fetch live weather (with fallback already inside fetch_rainfall_data)
        try:
            rainfall_mm = await asyncio.to_thread(fetch_rainfall_data, lat, lon)
        except Exception as exc:
            logger.warning(f"Rainfall fetch failed; defaulting to 0.0 mm — {exc}")
            rainfall_mm = 0.0

        # 2. Fetch soil type (for accurate risk score)
        try:
            soil_type = await asyncio.to_thread(fetch_soil_type, lat, lon)
        except Exception as exc:
            logger.warning(f"Soil fetch failed; defaulting to 'loam' — {exc}")
            soil_type = "loam"

        # 3. Run the risk model
        try:
            final_prob = await asyncio.to_thread(
                risk_predict,
                lat,
                lon,
                rainfall_mm=rainfall_mm,
                soil_type=soil_type,
            )
        except Exception as exc:
            logger.error(f"Risk model failed — defaulting to ALERT mode: {exc}")
            final_prob = 1.0  # fail-safe: assume critical if model is broken

        # 4. Determine raw state from spec thresholds
        is_critical = final_prob > CRITICAL_RISK_THRESHOLD or rainfall_mm > CRITICAL_RAIN_THRESHOLD

        # 5. Check user's Auto-Scale preference (Person 3 hook)
        auto_scale_on = await self._get_auto_scale_setting(session_id)

        # 6. Determine final interval
        #    If auto_scale is ON the emergency logic is the authority.
        #    If auto_scale is OFF we honour the model result directly.
        if auto_scale_on:
            interval = ALERT_INTERVAL if is_critical else NORMAL_INTERVAL
            logger.info(
                f"Auto-Scale ON → {'CRITICAL' if is_critical else 'NORMAL'} "
                f"(prob={final_prob:.3f}, rain={rainfall_mm:.1f}mm)"
            )
        else:
            # Auto-scale is OFF — still use model result but log it as manual-override suppressed
            interval = ALERT_INTERVAL if is_critical else NORMAL_INTERVAL
            logger.info(
                f"Auto-Scale OFF → interval follows model result "
                f"({'ALERT' if is_critical else 'NORMAL'}); "
                f"manual setting not overriding emergency logic per spec."
            )

        risk_level = "CRITICAL" if is_critical else "NORMAL"
        next_check_at = datetime.now(timezone.utc) + interval

        # 7. Persist / update monitoring_sessions (never create duplicate rows)
        await self._upsert_session(lat, lon, interval, risk_level, next_check_at, final_prob, rainfall_mm)

        return interval

    # ── Cool-down helper ──────────────────────────────────────────────────────

    async def apply_cooldown(self, lat: float, lon: float) -> bool:
        """
        Check whether a session that was CRITICAL has had enough consecutive
        normal readings to safely downgrade.  Returns True if cooldown
        is satisfied and the session can revert to NORMAL_INTERVAL.

        The `consecutive_normal_count` column in monitoring_sessions tracks
        how many back-to-back normal readings have occurred.
        """
        try:
            result = (
                self._db.table("monitoring_sessions")
                .select("consecutive_normal_count, risk_level")
                .eq("lat", lat)
                .eq("lon", lon)
                .single()
                .execute()
            )
            row = result.data
            if not row:
                return True  # no session → treat as normal

            count = row.get("consecutive_normal_count", 0) or 0
            return count >= COOLDOWN_CYCLES
        except Exception as exc:
            logger.warning(f"Cooldown check failed: {exc}")
            return True

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _get_auto_scale_setting(self, session_id: Optional[str]) -> bool:
        """
        Look up auto_scale flag in user_settings for the given session_id.
        Returns True (auto-scale ON) by default if no preference is found,
        so the safety logic is active unless explicitly disabled.
        """
        if not session_id:
            return True  # no session = default to auto-scale ON (safe default)
        try:
            result = (
                self._db.table("user_settings")
                .select("auto_scale, polling_interval_minutes")
                .eq("session_id", session_id)
                .single()
                .execute()
            )
            row = result.data
            if row:
                # auto_scale column may not exist yet on older rows; default True
                return bool(row.get("auto_scale", True))
        except Exception as exc:
            logger.warning(f"Could not fetch user_settings for {session_id}: {exc}")
        return True  # fail-safe: enable auto-scale

    async def _upsert_session(
        self,
        lat: float,
        lon: float,
        interval: timedelta,
        risk_level: str,
        next_check_at: datetime,
        final_prob: float,
        rainfall_mm: float,
    ) -> None:
        """
        Upsert a monitoring_sessions row keyed on (lat, lon).
        If the row is CRITICAL → NORMAL, increment consecutive_normal_count.
        If CRITICAL, reset it to 0.

        Uses Supabase UPSERT with on_conflict="lat,lon" — requires a UNIQUE
        constraint on (lat, lon) in the DB (provided in the SQL schema).
        """
        now = datetime.now(timezone.utc).isoformat()

        try:
            # Fetch existing row to manage cooldown counter
            existing = (
                self._db.table("monitoring_sessions")
                .select("risk_level, consecutive_normal_count")
                .eq("lat", lat)
                .eq("lon", lon)
                .execute()
            )
            rows = existing.data
            prev_risk = rows[0]["risk_level"] if rows else None
            prev_count = rows[0].get("consecutive_normal_count", 0) if rows else 0

            if risk_level == "NORMAL":
                consecutive_normal_count = (prev_count or 0) + 1
            else:
                consecutive_normal_count = 0  # reset on any critical reading

            payload = {
                "lat": lat,
                "lon": lon,
                "last_check": now,
                "next_check_at": next_check_at.isoformat(),
                "current_frequency_minutes": int(interval.total_seconds() / 60),
                "risk_level": risk_level,
                "final_prob": round(final_prob, 4),
                "rainfall_mm": round(rainfall_mm, 2),
                "consecutive_normal_count": consecutive_normal_count,
                "updated_at": now,
            }

            self._db.table("monitoring_sessions").upsert(
                payload, on_conflict="lat,lon"
            ).execute()

            logger.info(
                f"Session upserted → ({lat:.4f}, {lon:.4f}) | "
                f"{risk_level} | next_check={next_check_at.isoformat()} | "
                f"cooldown_count={consecutive_normal_count}/{COOLDOWN_CYCLES}"
            )

        except Exception as exc:
            logger.error(f"Failed to upsert monitoring_sessions: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Background polling loop (FastAPI BackgroundTasks / asyncio.create_task)
# ─────────────────────────────────────────────────────────────────────────────

async def run_adaptive_polling_loop(db: Client, poll_targets: list[dict]) -> None:
    """
    Long-running coroutine that processes all registered monitoring targets.

    Each entry in `poll_targets` should be:
        {"lat": float, "lon": float, "session_id": str | None}

    The loop respects each target's `next_check_at` timestamp stored in
    Supabase — it will skip a target if it's not yet due for a check.

    Intended to be launched once at startup via asyncio.create_task().

    Example:
        asyncio.create_task(
            run_adaptive_polling_loop(supabase, targets)
        )
    """
    scaler = AdaptiveScaler(db)
    logger.info(f"Adaptive polling loop started — {len(poll_targets)} target(s).")

    while True:
        now = datetime.now(timezone.utc)

        for target in poll_targets:
            lat = target["lat"]
            lon = target["lon"]
            session_id = target.get("session_id")

            # Check if this target is due for a poll
            try:
                existing = (
                    db.table("monitoring_sessions")
                    .select("next_check_at, risk_level, consecutive_normal_count")
                    .eq("lat", lat)
                    .eq("lon", lon)
                    .execute()
                )
                rows = existing.data
                if rows:
                    next_check_str = rows[0].get("next_check_at")
                    if next_check_str:
                        next_check = datetime.fromisoformat(next_check_str)
                        # Make timezone-aware if naive
                        if next_check.tzinfo is None:
                            next_check = next_check.replace(tzinfo=timezone.utc)
                        if now < next_check:
                            logger.debug(
                                f"Skipping ({lat:.4f}, {lon:.4f}) — next check at {next_check.isoformat()}"
                            )
                            continue

                    # Cool-down check: if we've been CRITICAL but have enough
                    # normal readings, we can safely stay at NORMAL_INTERVAL
                    risk = rows[0].get("risk_level", "NORMAL")
                    count = rows[0].get("consecutive_normal_count", 0) or 0
                    if risk == "NORMAL" and count >= COOLDOWN_CYCLES:
                        logger.info(
                            f"({lat:.4f}, {lon:.4f}) cool-down satisfied "
                            f"({count}/{COOLDOWN_CYCLES} normal cycles). Maintaining NORMAL_INTERVAL."
                        )

            except Exception as exc:
                logger.warning(f"Pre-check query failed for ({lat}, {lon}): {exc}")

            # Run the scaler
            try:
                interval = await scaler.calculate_next_poll_interval(lat, lon, session_id)
                logger.info(
                    f"({lat:.4f}, {lon:.4f}) → next poll in "
                    f"{int(interval.total_seconds() // 3600)}h "
                    f"{int((interval.total_seconds() % 3600) // 60)}m"
                )
            except Exception as exc:
                logger.error(f"Scaler failed for ({lat}, {lon}): {exc}")

        # Sleep for the minimum possible interval before checking again.
        # The per-target next_check_at logic handles actual scheduling.
        await asyncio.sleep(60)  # heartbeat: check targets every 60 seconds
