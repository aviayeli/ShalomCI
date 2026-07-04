from src.gui.auth import auth_enabled, check_credentials


def test_auth_enabled_false_when_password_unset(monkeypatch):
    """אימות כבוי כשאין SHALOMCI_PASSWORD - האפליקציה רצה ללא מסך התחברות."""
    monkeypatch.delenv("SHALOMCI_PASSWORD", raising=False)
    assert auth_enabled() is False


def test_auth_enabled_false_when_password_empty(monkeypatch):
    """מחרוזת ריקה אינה מפעילה אימות (opt-in מפורש בלבד)."""
    monkeypatch.setenv("SHALOMCI_PASSWORD", "")
    assert auth_enabled() is False


def test_auth_enabled_true_when_password_set(monkeypatch):
    """סיסמה לא-ריקה מפעילה את שער ההתחברות."""
    monkeypatch.setenv("SHALOMCI_PASSWORD", "s3cret")
    assert auth_enabled() is True


def test_check_credentials_accepts_correct_user_and_password(monkeypatch):
    """שם משתמש וסיסמה נכונים -> True."""
    monkeypatch.setenv("SHALOMCI_USERNAME", "avi")
    monkeypatch.setenv("SHALOMCI_PASSWORD", "s3cret")
    assert check_credentials("avi", "s3cret") is True


def test_check_credentials_rejects_wrong_password(monkeypatch):
    """סיסמה שגויה -> False."""
    monkeypatch.setenv("SHALOMCI_USERNAME", "avi")
    monkeypatch.setenv("SHALOMCI_PASSWORD", "s3cret")
    assert check_credentials("avi", "wrong") is False


def test_check_credentials_rejects_wrong_username(monkeypatch):
    """שם משתמש שגוי -> False."""
    monkeypatch.setenv("SHALOMCI_USERNAME", "avi")
    monkeypatch.setenv("SHALOMCI_PASSWORD", "s3cret")
    assert check_credentials("intruder", "s3cret") is False


def test_check_credentials_default_username_is_admin(monkeypatch):
    """משתמש ברירת מחדל 'admin' עובד כאשר SHALOMCI_USERNAME לא הוגדר."""
    monkeypatch.delenv("SHALOMCI_USERNAME", raising=False)
    monkeypatch.setenv("SHALOMCI_PASSWORD", "s3cret")
    assert check_credentials("admin", "s3cret") is True


def test_check_credentials_rejects_empty_inputs_when_configured(monkeypatch):
    """קלט ריק נדחה כאשר אימות מוגדר (מונע כניסה בטופס ריק)."""
    monkeypatch.setenv("SHALOMCI_USERNAME", "avi")
    monkeypatch.setenv("SHALOMCI_PASSWORD", "s3cret")
    assert check_credentials("", "") is False
