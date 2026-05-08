"""
chatbot_service.py
==================
Bridges the AroundU backend with the external Beni Suef chatbot AI service.

Responsibilities
----------------
1. check_health()        – probe AI service liveness
2. chat()                – enrich request with user context, relay to AI, log result,
                           and optionally fire a recommendation notification
3. _build_context()      – internal: gather recent interactions + favorites from DB
4. _log_interaction()    – internal: persist to ai_interactions table
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional
from uuid import uuid4

import httpx
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.logger import logger
from src.models.ai_interaction import AIInteraction
from src.models.notification import NotificationType, NotificationPriority

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

CHATBOT_BASE_URL = settings.CHATBOT_SERVICE_URL
_TIMEOUT         = httpx.Timeout(settings.CHATBOT_TIMEOUT_SECONDS, connect=5.0)
_FALLBACK_REPLY  = (
    "Sorry, I'm having trouble connecting right now. "
    "Please try again in a moment. 🙏"
)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

async def check_health() -> dict:
    """
    Probe the external chatbot service.
    Returns the raw health JSON or a degraded status dict.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{CHATBOT_BASE_URL}/health")
            res.raise_for_status()
            return res.json()
    except Exception as exc:
        logger.warning(f"[chatbot] Health check failed: {exc}")
        return {"status": "unhealthy", "models_loaded": False}


async def chat(
    db: Session,
    user_id: int,
    user_role: str,
    message: str,
    session_id: Optional[str] = None,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    background_tasks: Optional[BackgroundTasks] = None,
) -> dict:
    """
    Main entry point called by the API router.

    1. Builds rich user context from DB
    2. Sends enriched request to /chat
    3. Persists the interaction
    4. Optionally fires a recommendation push notification
    5. Returns cleaned response dict
    """
    if not session_id:
        session_id = str(uuid4())

    # Build context (non-blocking DB reads)
    context = _build_context(db, user_id, user_role, user_lat, user_lon)

    # ── RAG: Inject local knowledge into the message ────────────────────────
    # We fetch real places *before* calling the AI so it knows about them.
    knowledge_block = _build_knowledge_block(db, message, user_lat, user_lon)
    
    if knowledge_block:
        enriched_message = f"{message}\n\n[LOCAL_INFO: {knowledge_block}]"
    else:
        enriched_message = message

    payload = {
        "message":    enriched_message,
        "session_id": session_id,
        "user_lat":   user_lat,
        "user_lon":   user_lon,
    }

    t0 = time.monotonic()
    ai_data, is_fallback = await _call_chatbot(payload)
    latency_ms = int((time.monotonic() - t0) * 1000)

    # Persist in background — wrap coroutine in a sync helper for BackgroundTasks
    def _run_log():
        asyncio.create_task(
            _log_interaction(
                db=db,
                user_id=user_id,
                session_id=session_id,
                message=message,
                user_lat=user_lat,
                user_lon=user_lon,
                ai_data=ai_data,
                latency_ms=latency_ms,
                is_fallback=is_fallback,
            )
        )

    if background_tasks:
        background_tasks.add_task(_run_log)
    else:
        asyncio.create_task(
            _log_interaction(
                db=db,
                user_id=user_id,
                session_id=session_id,
                message=message,
                user_lat=user_lat,
                user_lon=user_lon,
                ai_data=ai_data,
                latency_ms=latency_ms,
                is_fallback=is_fallback,
            )
        )

    # ── Grounding: Override AI suggestion with real local data ────────────────
    best_place = ai_data.get("best_place")
    intent     = ai_data.get("intent", "fallback")

    if not is_fallback:
        local_match = _find_local_place_match(
            db=db,
            ai_data=ai_data,
            query_text=message,
            user_lat=user_lat,
            user_lon=user_lon,
            user_id=user_id,
        )
        if local_match:
            best_place = local_match
            if intent == "fallback":
                ai_data["intent"] = "nearest_place"
                ai_data["reply"] = f"ليقيتلك '{local_match['name']}' في بني سويف، ينفعك؟"

    # Attach full menu (subcategories + items with images) to best_place
    if best_place:
        place_id_for_menu = best_place.get("id") or best_place.get("place_id")
        if place_id_for_menu:
            try:
                place_id_int = int(place_id_for_menu)
                best_place["menu"] = _get_place_menu(db, place_id_int)
            except Exception as menu_exc:
                logger.warning(f"[chatbot] Could not fetch menu for place {place_id_for_menu}: {menu_exc}")
                best_place["menu"] = []

    # Fire recommendation notification if we have a valid place
    if best_place and not is_fallback and background_tasks:
        place_id = best_place.get("id") or best_place.get("place_id")
        if place_id:
            background_tasks.add_task(
                _send_recommendation_notification,
                user_id=user_id,
                place_id=place_id,
                place_name=best_place.get("name", "a place"),
            )

    return {
        "reply":      ai_data.get("reply", _FALLBACK_REPLY),
        "intent":     ai_data.get("intent", "unknown"),
        "confidence": ai_data.get("confidence", 0.0),
        "entities":   ai_data.get("entities", {}),
        "best_place": best_place,
        "session_id": ai_data.get("session_id", session_id),
        "is_fallback": is_fallback,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Internal Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _get_place_menu(db: Session, place_id: int) -> list:
    """
    Returns the full menu for a place as a list of subcategories,
    each containing a list of available items (with image_url).
    Example output:
    [
      {
        "id": 1,
        "name": "برجر",
        "items": [
          {"id": 5, "name": "برجر كلاسيك", "price": 89, "image_url": "...", "is_available": true}
        ]
      },
      ...
    ]
    """
    from sqlalchemy import text
    menu = []
    try:
        # Fetch non-deleted subcategories for this place
        subcats = db.execute(
            text("""
                SELECT id, name
                FROM subcategories
                WHERE place_id = :pid AND is_deleted = FALSE
                ORDER BY id
            """),
            {"pid": place_id},
        ).fetchall()

        for sub in subcats:
            sub_id, sub_name = sub[0], sub[1]
            # Fetch available, non-deleted items for this subcategory
            items = db.execute(
                text("""
                    SELECT id, name, description, price, image_url, is_available
                    FROM items
                    WHERE sub_category_id = :sid
                      AND (is_deleted IS NULL OR is_deleted = FALSE)
                      AND (is_available IS NULL OR is_available = TRUE)
                    ORDER BY id
                """),
                {"sid": sub_id},
            ).fetchall()

            menu.append({
                "id":    sub_id,
                "name":  sub_name,
                "items": [
                    {
                        "id":           row[0],
                        "name":         row[1],
                        "description":  row[2],
                        "price":        float(row[3]) if row[3] else None,
                        "image_url":    row[4],
                        "is_available": bool(row[5]) if row[5] is not None else True,
                    }
                    for row in items
                ],
            })
    except Exception as exc:
        logger.warning(f"[chatbot] _get_place_menu failed for place {place_id}: {exc}")
    return menu

async def _call_chatbot(payload: dict) -> tuple[dict, bool]:
    """
    Makes the HTTP call to the external AI service.
    Never raises — returns (fallback_dict, True) on any failure.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            res = await client.post(f"{CHATBOT_BASE_URL}/chat", json=payload)
            res.raise_for_status()
            return res.json(), False
    except httpx.HTTPStatusError as exc:
        logger.warning(
            f"[chatbot] AI service returned {exc.response.status_code}: "
            f"{exc.response.text[:200]}"
        )
    except httpx.RequestError as exc:
        logger.error(f"[chatbot] Network error reaching AI service: {exc}")
    except Exception as exc:
        logger.error(f"[chatbot] Unexpected error: {exc}", exc_info=True)

    return {"reply": _FALLBACK_REPLY}, True


def _build_context(
    db: Session,
    user_id: int,
    user_role: str,
    user_lat: Optional[float],
    user_lon: Optional[float],
) -> dict:
    """
    Builds a rich context dict to enrich AI requests.
    Uses raw SQL to keep it lightweight and avoid model coupling.
    """
    from sqlalchemy import text

    context: dict = {
        "user_id":   user_id,
        "user_role": user_role,
    }

    # ── Recent interactions (last 5 places visited/saved) ────────────────────
    try:
        rows = db.execute(
            text(
                """
                SELECT i.place_id, p.name, i.type, i.created_at
                FROM interactions i
                JOIN places p ON p.id = i.place_id
                WHERE i.user_id = :uid
                ORDER BY i.created_at DESC
                LIMIT 5
                """
            ),
            {"uid": user_id},
        ).fetchall()

        context["recent_interactions"] = [
            {
                "place_id":   r[0],
                "place_name": r[1],
                "type":       r[2],
                "at":         r[3].isoformat() if r[3] else None,
            }
            for r in rows
        ]
    except Exception as exc:
        logger.warning(f"[chatbot] Could not fetch recent interactions: {exc}")
        context["recent_interactions"] = []

    # ── Preferred / favorited places ─────────────────────────────────────────
    try:
        fav_rows = db.execute(
            text(
                """
                SELECT p.id, p.name, p.category_id
                FROM favorites f
                JOIN places p ON p.id = f.place_id
                WHERE f.user_id = :uid
                LIMIT 10
                """
            ),
            {"uid": user_id},
        ).fetchall()

        context["preferred_places"] = [
            {"place_id": r[0], "name": r[1], "category_id": r[2]}
            for r in fav_rows
        ]
    except Exception as exc:
        logger.warning(f"[chatbot] Could not fetch favorites: {exc}")
        context["preferred_places"] = []

    # ── Location hint ─────────────────────────────────────────────────────────
    if user_lat is not None and user_lon is not None:
        context["user_location"] = {"lat": user_lat, "lon": user_lon}

    return context


async def _log_interaction(
    db: Session,
    user_id: int,
    session_id: str,
    message: str,
    user_lat: Optional[float],
    user_lon: Optional[float],
    ai_data: dict,
    latency_ms: int,
    is_fallback: bool,
) -> None:
    """Persist the exchange to ai_interactions. Fire-and-forget."""
    from src.core.database import SessionLocal

    async_db = SessionLocal()
    try:
        record = AIInteraction(
            user_id    = user_id,
            session_id = session_id,
            message    = message,
            user_lat   = user_lat,
            user_lon   = user_lon,
            reply      = ai_data.get("reply"),
            intent     = ai_data.get("intent"),
            confidence = ai_data.get("confidence"),
            entities   = ai_data.get("entities"),
            best_place = ai_data.get("best_place"),
            latency_ms = latency_ms,
            is_fallback = int(is_fallback),
        )
        async_db.add(record)
        async_db.commit()
    except Exception as exc:
        logger.error(f"[chatbot] Failed to log AI interaction: {exc}")
        async_db.rollback()
    finally:
        async_db.close()


def _translate_category(arabic_name: str) -> str:
    """
    Maps Arabic category names from AI to English names in our Database.
    """
    if not arabic_name:
        return ""
    
    mapping = {
        "مطعم": "Restaurant",
        "restaurant": "Restaurant",
        "أكل": "Restaurant",
        "كافيه": "Cafe",
        "cafe": "Cafe",
        "مقهى": "Cafe",
        "قهوة": "Cafe",
        "صيدلية": "Pharmacy",
        "pharmacy": "Pharmacy",
        "سوبر ماركت": "Supermarket",
        "supermarket": "Supermarket",
        "بقالة": "Supermarket",
        "فندق": "Hotel",
        "hotel": "Hotel",
        "مستشفى": "Hospital",
        "hospital": "Hospital",
        "بنك": "Bank",
        "bank": "Bank",
        "معلم": "Landmark",
        "landmark": "Landmark",
        "أثر": "Landmark",
        "محطة": "Station",
        "station": "Station",
    }
    # Direct match or partial match
    for ar, en in mapping.items():
        if ar in arabic_name:
            return en
    return arabic_name


def _build_knowledge_block(
    db: Session,
    query: str,
    user_lat: Optional[float],
    user_lon: Optional[float]
) -> str:
    """
    Fetches the top 5 most relevant places and formats them as a string
    to be injected into the AI's prompt.
    """
    from src.repositories.place_repository import PlaceRepository
    repo = PlaceRepository(db)

    # Try to detect category from query to help the search
    detected_cat_en = _translate_category(query)
    
    try:
        # Get matching category ID if possible
        cat_id = None
        if detected_cat_en:
            from src.models.category import Category
            cat_row = db.query(Category).filter(Category.name.ilike(f"%{detected_cat_en}%")).first()
            if cat_row:
                cat_id = cat_row.id

        # Get 5 most relevant/nearby places
        results = repo.search_v2(
            q=query,
            lat=user_lat,
            lng=user_lon,
            limit=5
        )
        
        # If search_v2 is weak on Arabic, fallback to get_nearby with cat_id
        if (not results or len(results) < 2) and user_lat and user_lon:
            results = repo.get_nearby(user_lat, user_lon, radius_km=10.0, category_id=cat_id, limit=5)

        if not results:
            return ""

        # Format as simple bullet points for the AI
        lines = []
        for p in results:
            # Include name and category for the AI to refer to
            info = f"- {p['name']} (تصنيف: {p.get('category', 'غير محدد')})"
            if p.get('distance'):
                dist = p['distance']
                info += f" - يبعد عنك حوالي {int(dist)} متر"
            lines.append(info)
        
        return "\n".join(lines)

    except Exception as exc:
        logger.warning(f"[chatbot] Knowledge retrieval failed: {exc}")
        return "Database search currently unavailable."


def _find_local_place_match(
    db: Session,
    ai_data: dict,
    query_text: str,
    user_lat: Optional[float],
    user_lon: Optional[float],
    user_id: Optional[int] = None,
) -> Optional[dict]:
    """
    Tries to find the most relevant place in OUR database.
    Now supports searching based on the original query text if AI falls back.
    """
    from src.repositories.place_repository import PlaceRepository
    from src.models.category import Category

    from sqlalchemy import or_
    intent   = ai_data.get("intent", "").lower()
    entities = ai_data.get("entities", {})
    ai_cat_arabic = entities.get("category") or ""
    
    # Improved keyword detection including English terms
    if intent == "fallback" or not ai_cat_arabic:
        keywords = {
            "مطعم": ["مطعم", "أكل", "restaurant", "food", "hungry", "جائع"],
            "كافيه": ["كافيه", "قهوة", "مقهى", "cafe", "coffee", "drink", "شاي"],
            "سوبر ماركت": ["سوبر ماركت", "supermarket", " grocery", "بقالة", "تسوق"],
            "صيدلية": ["صيدلية", "دواء", "pharmacy", "medicine", "علاج"],
        }
        for ar_cat, kw_list in keywords.items():
            if any(kw in query_text.lower() for kw in kw_list):
                ai_cat_arabic = ar_cat
                break
    
    # Translate to English for DB search
    ai_cat_en = _translate_category(ai_cat_arabic)

    repo = PlaceRepository(db)

    # 1. Map category name to local category_id
    cat_id = None
    try:
        # More aggressive category matching: search for any category containing the term
        # and try both original and translated terms.
        cat_row = db.query(Category).filter(
            or_(
                Category.name.ilike(f"%{ai_cat_en}%"),
                Category.name.ilike(f"%{ai_cat_arabic}%")
            )
        ).first()
        
        if cat_row:
            cat_id = cat_row.id
    except Exception as exc:
        logger.warning(f"[chatbot] Aggressive category match failed: {exc}")

    # 2. Perform search based on intent
    try:
        results = []
        # If we have a category ID, try to find the nearest match in that category
        if cat_id and user_lat and user_lon:
            results = repo.get_nearby(
                latitude=user_lat,
                longitude=user_lon,
                radius_km=15.0,
                category_id=cat_id,
                limit=1
            )
        
        # If no category match, try a name-based search with the query
        if not results:
            query = ai_cat_arabic or query_text
            results = repo.search_v2(
                q=query,
                lat=user_lat,
                lng=user_lon,
                limit=1
            )

        if results:
            match = results[0]
            match["place_id"] = str(match["id"])

            # ── Enrich with full place details needed by the mobile UI ──────────
            try:
                from sqlalchemy import text as _text
                detail = db.execute(
                    _text("""
                        SELECT
                            p.address,
                            p.phone,
                            p.latitude,
                            p.longitude,
                            p.opening_hours,
                            p.is_open,
                            (
                                SELECT pi.image_url
                                FROM place_images pi
                                WHERE pi.place_id = p.id
                                  AND (pi.image_type = 'main' OR pi.image_type IS NULL)
                                ORDER BY pi.created_at ASC
                                LIMIT 1
                            ) AS main_image_url
                        FROM places p
                        WHERE p.id = :pid
                    """),
                    {"pid": match["id"]},
                ).fetchone()

                if detail:
                    match["address"]        = detail[0]
                    match["phone"]          = detail[1]
                    match["latitude"]       = float(detail[2]) if detail[2] else None
                    match["longitude"]      = float(detail[3]) if detail[3] else None
                    match["opening_hours"]  = detail[4]
                    match["is_open"]        = bool(detail[5]) if detail[5] is not None else None
                    match["main_image_url"] = detail[6]

                # is_favorited for the current user
                if user_id:
                    fav_row = db.execute(
                        _text("""
                            SELECT 1 FROM favorites
                            WHERE user_id = :uid AND place_id = :pid
                            LIMIT 1
                        """),
                        {"uid": user_id, "pid": match["id"]},
                    ).fetchone()
                    match["is_favorited"] = fav_row is not None
                else:
                    match["is_favorited"] = False

                # distance_km if location was provided
                if user_lat and user_lon and match.get("latitude") and match.get("longitude"):
                    dist_row = db.execute(
                        _text("""
                            SELECT ST_Distance(
                                ST_SetSRID(ST_MakePoint(:plon, :plat), 4326)::geography,
                                ST_SetSRID(ST_MakePoint(:ulon, :ulat), 4326)::geography
                            ) / 1000.0 AS distance_km
                        """),
                        {
                            "plat": match["latitude"], "plon": match["longitude"],
                            "ulat": user_lat,          "ulon": user_lon,
                        },
                    ).fetchone()
                    match["distance_km"] = round(float(dist_row[0]), 2) if dist_row else None
                else:
                    match["distance_km"] = None

            except Exception as enrich_exc:
                logger.warning(f"[chatbot] Could not enrich place details: {enrich_exc}")

            return match

    except Exception as exc:
        logger.error(f"[chatbot] Grounding search failed: {exc}")

    return None


async def _send_recommendation_notification(
    user_id: int,
    place_id: int,
    place_name: str,
) -> None:
    """
    Fires a recommendation push notification after AI suggests a place.
    Uses a fresh DB session to stay outside the request lifecycle.
    """
    from src.core.database import SessionLocal
    from src.core.unit_of_work import UnitOfWork
    from src.services.notification_service import create_notification

    try:
        uow = UnitOfWork(SessionLocal)
        await create_notification(
            uow=uow,
            user_id=user_id,
            title="Suggested for you 🔥",
            message=f"We think you'll love {place_name}! Check it out.",
            notif_type=NotificationType.SYSTEM_ALERT,
            priority=NotificationPriority.NORMAL,
            data={"place_id": str(place_id), "source": "chatbot"},
        )
        logger.info(
            f"[chatbot] Recommendation notification sent → user={user_id}, place={place_id}"
        )
    except Exception as exc:
        logger.error(f"[chatbot] Recommendation notification failed: {exc}")
