"""
session_buffer.py
─────────────────
In-memory buffer that accumulates face-recognition matches during an
attendance session and flushes them to the database in ONE bulk write
using raw psycopg2 execute_values for performance.

Confidence values are cosine-similarity scores (0–1, higher = better match).
This applies to live scan, kiosk scan, and group-photo flows.

Usage:
    buf = SessionBuffer(session_id)
    for user in detected_users:
        buf.add(user_id, confidence=0.85)  # cosine similarity

    # Group flow — one bulk DB write
    present, absent = buf.flush_attendance(enrolled_students)
    # Live / kiosk flow — flush live records then transfer to permanent log
    buf.flush_live_records()
"""

import logging
from django.db import connection, transaction
import psycopg2.extras
from django.utils import timezone
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

# Global memory buffer for live sessions
# Format: { session_id : SessionBuffer_instance }
_LIVE_BUFFERS = {}

def get_live_buffer(session_id):
    sid = str(session_id)
    if sid not in _LIVE_BUFFERS:
        _LIVE_BUFFERS[sid] = SessionBuffer(sid)
    return _LIVE_BUFFERS[sid]

def clear_live_buffer(session_id):
    sid = str(session_id)
    if sid in _LIVE_BUFFERS:
        del _LIVE_BUFFERS[sid]

class SessionBuffer:
    """
    Accumulates recognised faces in memory.
    Deduplicates by student — keeping only the highest confidence per student.
    """

    def __init__(self, session_id_val):
        self.session_id_val = session_id_val
        self._matches = {}
        self._flushed = False

    def add(self, user_id, confidence=1.0):
        if user_id not in self._matches or confidence > self._matches[user_id]:
            self._matches[user_id] = confidence

    @property
    def matched_user_ids(self):
        return set(self._matches.keys())

    def flush_live_records(self):
        """
        ONE single bulk INSERT to PostgreSQL via psycopg2 for live/kiosk scan.
        confidence = cosine similarity (higher is better).
        Deduplicates via ON CONFLICT DO UPDATE SET confidence = GREATEST(...).
        """
        if self._flushed or not self._matches:
            return 0
            
        now = timezone.now()
        data = []
        for uid, conf in self._matches.items():
            # live_session_id, student_id, scanned_at, confidence
            data.append((self.session_id_val, uid, now, conf))
            
        with connection.cursor() as cursor:
            if connection.vendor == 'postgresql':
                import psycopg2.extras
                query = """
                    INSERT INTO accounts_liveattendancerecord 
                    (live_session_id, student_id, scanned_at, confidence)
                    VALUES %s
                    ON CONFLICT (live_session_id, student_id)
                    DO UPDATE SET 
                        confidence = GREATEST(accounts_liveattendancerecord.confidence, EXCLUDED.confidence),
                        scanned_at = EXCLUDED.scanned_at
                """
                psycopg2.extras.execute_values(cursor.cursor, query, data)
            else:
                # SQLite fallback (dev environment)
                query = """
                    INSERT INTO accounts_liveattendancerecord 
                    (live_session_id, student_id, scanned_at, confidence)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT(live_session_id, student_id) 
                    DO UPDATE SET 
                        confidence = MAX(confidence, excluded.confidence),
                        scanned_at = excluded.scanned_at
                """
                for row in data:
                    cursor.execute(query, row)
                
        logger.info(
            "LiveSessionBuffer flushed: %d records in 1 DB call (live session=%s)",
            len(data), self.session_id_val
        )
        self._flushed = True
        return len(data)

    def flush_attendance(self, enrolled_students=None, full_session_obj=None):
        """
        Writes attendance (Present/Absent records) in one bulk DB call using psycopg2.
        Returns: (present_list, absent_list) of (User, bool)
        """
        if self._flushed:
             return [], []
             
        present_list = []
        absent_list = []
        data = []
        # Convert time to string format to prevent SQLite binding errors
        now_str = str(timezone.now().time())
        
        if enrolled_students:
            for student in enrolled_students:
                is_present = student.id in self._matches
                # session_id, student_id, status, time_marked
                data.append((self.session_id_val, student.id, is_present, now_str))
                if student.email:
                    if is_present: present_list.append((student, True))
                    else: absent_list.append((student, False))
        else:
            # Fallback if no specific enrollment passed
            for uid in self._matches.keys():
                data.append((self.session_id_val, uid, True, now_str))
                try:
                    u = User.objects.get(id=uid)
                    present_list.append((u, True))
                except: pass
                
        if data:
            with connection.cursor() as cursor:
                if connection.vendor == 'postgresql':
                    import psycopg2.extras
                    query = """
                        INSERT INTO accounts_attendance 
                        (session_id, student_id, status, time_marked)
                        VALUES %s
                        ON CONFLICT (session_id, student_id)
                        DO UPDATE SET 
                            status = EXCLUDED.status,
                            time_marked = EXCLUDED.time_marked
                    """
                    psycopg2.extras.execute_values(cursor.cursor, query, data)
                else: 
                    # SQLite fallback
                    query = """
                        INSERT INTO accounts_attendance 
                        (session_id, student_id, status, time_marked)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (session_id, student_id)
                        DO UPDATE SET 
                            status = excluded.status,
                            time_marked = excluded.time_marked
                    """
                    cursor.executemany(query, data)
                    
            logger.info(f"Attendance SessionBuffer flushed: {len(data)} records in 1 DB call (session={self.session_id_val})")
            
        self._flushed = True
        self._matches.clear()
        return present_list, absent_list

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def __len__(self):
        return len(self._matches)
