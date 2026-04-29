import hashlib
import unittest
from unittest.mock import patch

from app.routers.auth import login_for_access_token
from app.schemas.auth import LoginRequest
from app.schemas.users import User
from app.security import hash_password, pwd_context, verify_and_upgrade_password
from app.services.a_service import insert_user, update_user_service


class PasswordMigrationTests(unittest.TestCase):
    def test_verify_and_upgrade_bcrypt_keeps_existing_hash(self):
        stored_hash = pwd_context.hash("Secret123!")

        is_valid, upgraded_hash = verify_and_upgrade_password("Secret123!", stored_hash)

        self.assertTrue(is_valid)
        self.assertIsNone(upgraded_hash)

    def test_verify_and_upgrade_plaintext_generates_bcrypt_hash(self):
        is_valid, upgraded_hash = verify_and_upgrade_password("Secret123!", "Secret123!")

        self.assertTrue(is_valid)
        self.assertIsNotNone(upgraded_hash)
        self.assertTrue(pwd_context.verify("Secret123!", upgraded_hash))

    def test_verify_and_upgrade_md5_generates_bcrypt_hash(self):
        legacy_md5 = hashlib.md5("Secret123!".encode("utf-8")).hexdigest()

        is_valid, upgraded_hash = verify_and_upgrade_password("Secret123!", legacy_md5)

        self.assertTrue(is_valid)
        self.assertIsNotNone(upgraded_hash)
        self.assertTrue(pwd_context.verify("Secret123!", upgraded_hash))

    def test_hash_password_keeps_bcrypt_inputs(self):
        stored_hash = pwd_context.hash("Secret123!")

        self.assertEqual(hash_password(stored_hash), stored_hash)


class UserPersistenceTests(unittest.TestCase):
    @patch("app.services.a_service.run_query", return_value=101)
    def test_insert_user_hashes_plaintext_before_persisting(self, mock_run_query):
        data = User(id_person=1, id_company=None, id_role=2, password_hash="Secret123!")

        insert_user(data)

        _, params = mock_run_query.call_args.args[:2]
        self.assertNotEqual(params[3], "Secret123!")
        self.assertTrue(pwd_context.verify("Secret123!", params[3]))

    @patch("app.services.a_service.run_query")
    def test_update_user_hashes_plaintext_before_persisting(self, mock_run_query):
        data = User(id_person=1, id_company=7, id_role=2, password_hash="Secret123!")

        update_user_service(55, data)

        _, params = mock_run_query.call_args.args[:2]
        self.assertNotEqual(params[3], "Secret123!")
        self.assertEqual(params[4], 55)
        self.assertTrue(pwd_context.verify("Secret123!", params[3]))


class LoginEndpointTests(unittest.TestCase):
    @patch("app.routers.auth.create_access_token", return_value="jwt-token")
    @patch("app.routers.auth.run_query")
    def test_login_upgrades_legacy_md5_hash_after_successful_auth(self, mock_run_query, _mock_token):
        legacy_md5 = hashlib.md5("Secret123!".encode("utf-8")).hexdigest()
        user_row = {
            "id_user": 88,
            "id_person": 9,
            "id_company": 3,
            "id_role": 2,
            "password_hash": legacy_md5,
            "name": "Ana",
            "lastname": "Parra",
            "email": "ana@example.com",
        }
        mock_run_query.side_effect = [
            [user_row],
            None,
        ]

        response = login_for_access_token(
            LoginRequest(email="  ana@example.com  ", password="Secret123!")
        )

        self.assertEqual(response["access_token"], "jwt-token")
        self.assertEqual(mock_run_query.call_args_list[0].args[1], ("ana@example.com",))
        self.assertIn("UPDATE users SET password_hash", mock_run_query.call_args_list[1].args[0])
        upgraded_hash, target_user_id = mock_run_query.call_args_list[1].args[1]
        self.assertEqual(target_user_id, 88)
        self.assertTrue(pwd_context.verify("Secret123!", upgraded_hash))


if __name__ == "__main__":
    unittest.main()
