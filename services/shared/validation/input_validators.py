"""Reusable input validation helpers for browser-driven APIs."""

import re


EMAIL_RE = re.compile(r'^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$', re.IGNORECASE)
PHONE_RE = re.compile(r'^\d{10}$')
PINCODE_RE = re.compile(r'^\d{6}$')


def normalize_optional_text(value, max_length=None):
    text = str(value or '').strip()
    if max_length is not None:
        text = text[:max_length]
    return text


def normalize_email(value):
    return normalize_optional_text(value, 255).lower()


def normalize_phone(value):
    return re.sub(r'\D', '', str(value or ''))


def validate_name(value):
    name = normalize_optional_text(value, 100)
    if len(name) < 2:
        return False, 'Name must be at least 2 characters'
    return True, name


def validate_email(value):
    email = normalize_email(value)
    if not EMAIL_RE.match(email):
        return False, 'Invalid email format'
    return True, email


def validate_password(value):
    password = str(value or '')
    if len(password) < 8:
        return False, 'Password must be at least 8 characters'
    if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
        return False, 'Password must include at least one letter and one number'
    return True, password


def validate_phone(value, required=False):
    phone = normalize_phone(value)
    if not phone:
        if required:
            return False, 'Phone number is required'
        return True, ''
    if not PHONE_RE.match(phone):
        return False, 'Phone number must be 10 digits'
    return True, phone


def validate_pincode(value, required=False):
    pincode = re.sub(r'\D', '', str(value or ''))
    if not pincode:
        if required:
            return False, 'Pincode is required'
        return True, ''
    if not PINCODE_RE.match(pincode):
        return False, 'Pincode must be 6 digits'
    return True, pincode


def validate_registration_payload(data):
    sanitized = {}

    ok, result = validate_name(data.get('name'))
    if not ok:
        return False, result, None
    sanitized['name'] = result

    ok, result = validate_email(data.get('email'))
    if not ok:
        return False, result, None
    sanitized['email'] = result

    ok, result = validate_password(data.get('password'))
    if not ok:
        return False, result, None
    sanitized['password'] = result

    ok, result = validate_phone(data.get('phone'))
    if not ok:
        return False, result, None
    sanitized['phone'] = result

    ok, result = validate_pincode(data.get('pincode'))
    if not ok:
        return False, result, None
    sanitized['pincode'] = result

    sanitized['address'] = normalize_optional_text(data.get('address'), 255)
    sanitized['city'] = normalize_optional_text(data.get('city'), 100)
    sanitized['state'] = normalize_optional_text(data.get('state'), 100)
    return True, None, sanitized


def validate_profile_payload(data):
    sanitized = {}

    ok, result = validate_name(data.get('name'))
    if not ok:
        return False, result, None
    sanitized['name'] = result

    ok, result = validate_phone(data.get('phone'))
    if not ok:
        return False, result, None
    sanitized['phone'] = result

    ok, result = validate_pincode(data.get('pincode'))
    if not ok:
        return False, result, None
    sanitized['pincode'] = result

    sanitized['address'] = normalize_optional_text(data.get('address'), 255)
    sanitized['city'] = normalize_optional_text(data.get('city'), 100)
    sanitized['state'] = normalize_optional_text(data.get('state'), 100)
    return True, None, sanitized


def validate_shipping_payload(data):
    sanitized = {}

    ok, result = validate_name(data.get('name', 'Guest User'))
    if not ok:
        return False, result, None
    sanitized['name'] = result

    ok, result = validate_phone(data.get('phone'), required=True)
    if not ok:
        return False, result, None
    sanitized['phone'] = result

    ok, result = validate_pincode(data.get('pincode'), required=True)
    if not ok:
        return False, result, None
    sanitized['pincode'] = result

    address = normalize_optional_text(data.get('address'), 255)
    city = normalize_optional_text(data.get('city'), 100)
    state = normalize_optional_text(data.get('state'), 100)
    if not address:
        return False, 'Address is required', None
    if not city:
        return False, 'City is required', None
    if not state:
        return False, 'State is required', None

    sanitized['address'] = address
    sanitized['city'] = city
    sanitized['state'] = state
    sanitized['payment_method'] = normalize_optional_text(data.get('payment_method'), 30) or 'COD'
    return True, None, sanitized
