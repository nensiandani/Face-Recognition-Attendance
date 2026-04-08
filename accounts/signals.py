from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User


@receiver(post_save, sender='accounts.Profile')
def auto_compute_face_encoding(sender, instance, **kwargs):
    """
    Auto-compute face encoding whenever a Profile image is saved/updated.
    Runs in a background thread so it doesn't block the request.
    """
    if getattr(instance, 'skip_signal', False):
        return

    if not instance.image:
        return

    # Prevent infinite loop: if the only things updated were our encodings, do NOT compute again
    update_fields = kwargs.get('update_fields')
    if update_fields and set(update_fields).issubset({"face_encoding", "encoding_updated_at"}):
        return

    import threading

    def _compute():
        try:
            from .encoding_service import compute_and_save_encoding_for_profile
            # Reload fresh from DB to avoid stale instance state
            fresh = sender.objects.select_related('user').get(pk=instance.pk)
            ok = compute_and_save_encoding_for_profile(fresh)
            if ok:
                print(f"[SUCCESS] Auto-encoded: {fresh.user.username}")
            else:
                print(f"[WARN] Auto-encode failed: {fresh.user.username} (no face found?)")
        except Exception as exc:
            print(f"[ERROR] auto_compute_face_encoding error: {exc}")

    t = threading.Thread(target=_compute, daemon=True)
    t.start()
