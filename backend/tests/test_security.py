"""Password interoperability checks. Run: PYTHONPATH=backend python -m unittest discover -s backend/tests.

PHP CLI is required for independent WordPress bcrypt compatibility checks.
Reference: https://developer.wordpress.org/reference/functions/wp_hash_password/
and https://developer.wordpress.org/reference/functions/wp_check_password/
"""
import hashlib
import json
import subprocess
import unittest

from app.core.security import hash_password, verify_password
from passlib.hash import bcrypt, phpass


def php(code, *args):
    return subprocess.check_output(["php", "-r", code, *args], text=True).strip()


class PasswordTests(unittest.TestCase):
    def test_reads_wordpress_bcrypt(self):
        stored = php("echo '$wp'.password_hash(base64_encode(hash_hmac('sha384', $argv[1], 'wp-sha384', true)), PASSWORD_BCRYPT);", "correct-password")
        self.assertTrue(verify_password("correct-password", stored))
        self.assertFalse(verify_password("wrong-password", stored))
        self.assertFalse(verify_password(" correct-password ", stored))

    def test_writes_wordpress_compatible_hashes(self):
        for password in ["correct-password", "x" * 100, "密碼🔐", "\u00a0password\u00a0", "\x00 password \x00"]:
            with self.subTest(password=password):
                stored = hash_password(password)
                self.assertTrue(stored.startswith("$wp$2y$"))
                # Pass JSON so embedded NUL bytes can reach PHP safely.
                result = php("$p=trim(json_decode($argv[1])); echo password_verify(base64_encode(hash_hmac('sha384', $p, 'wp-sha384', true)), substr($argv[2], 3)) ? 'yes' : 'no';", json.dumps(password), stored)
                self.assertEqual(result, "yes")

    def test_legacy_hashes_still_work(self):
        for stored in [hashlib.md5(b"password").hexdigest(), phpass.hash("password"), bcrypt.hash("password")]:
            with self.subTest(stored=stored):
                self.assertTrue(verify_password("password", stored))
                self.assertFalse(verify_password("wrong", stored))

    def test_invalid_bcrypt_is_rejected(self):
        for stored in ["garbage", "$wp$2y$invalid", "$2y$invalid"]:
            self.assertFalse(verify_password("password", stored))
