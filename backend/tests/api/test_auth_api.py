import pytest

from tests.api.conftest import login


def post_code(client, identifier="+79991234567"):
    return client.post("/auth/code", json={"identifier": identifier})


def post_verify(client, identifier, code):
    return client.post("/auth/verify", json={"identifier": identifier, "code": code})


class TestRequestCode:
    def test_the_code_is_accepted_and_described(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        response = post_code(client, "8 (999) 123-45-67")

        # Assert
        assert response.status_code == 202
        assert response.json() == {
            "kind": "phone", "identifier": "+79991234567", "resend_after": 60, "dev_code": None,
        }  # fmt: skip

    def test_the_code_is_delivered_through_the_sender(self, client, sender):
        # Arrange: состояние задают фикстуры (client, sender)
        # Act
        post_code(client)

        # Assert
        assert sender.sent[0][:2] == ("phone", "+79991234567")

    def test_email_works_too(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        response = post_code(client, "  Alice@Example.COM ")

        # Assert
        assert response.json()["kind"] == "email" and response.json()["identifier"] == "alice@example.com"

    @pytest.mark.parametrize("identifier", ["", "   ", "abc", "12345", "not-an-email@", "+999"])
    def test_garbage_gets_422_with_a_readable_message(self, client, sender, identifier):
        # Arrange: фикстуры (client, sender) и параметры теста (identifier)
        # Act
        response = post_code(client, identifier)

        # Assert
        assert response.status_code == 422 and "телефон или почту" in response.json()["detail"]
        assert sender.sent == []

    def test_a_missing_identifier_gets_422(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        response = client.post("/auth/code", json={})

        # Assert
        assert response.status_code == 422

    def test_a_repeat_request_gets_429_with_retry_after(self, client):
        # Arrange
        post_code(client)

        # Act
        response = post_code(client)

        # Assert
        assert response.status_code == 429 and response.headers["Retry-After"] == "60"

    def test_the_hourly_cap_gets_429_with_an_hour_to_wait(self, make_client):
        # Arrange
        client = make_client(code_resend_seconds=0, code_max_per_hour=2)
        post_code(client), post_code(client)

        # Act
        response = post_code(client)

        # Assert
        assert response.status_code == 429 and response.headers["Retry-After"] == "3600"

    def test_a_failed_delivery_gets_502(self, client, sender):
        # Arrange
        sender.fail = True

        # Act
        response = post_code(client)

        # Assert
        assert response.status_code == 502

    def test_dev_mode_returns_the_code(self, make_client, sender):
        # Arrange
        client = make_client(dev_return_code=True)

        # Act
        body = post_code(client).json()

        # Assert
        assert body["dev_code"] == sender.last_code("+79991234567")


class TestVerifyCode:
    def test_the_right_code_gives_a_token_and_marks_a_new_user(self, client, sender):
        # Arrange
        post_code(client)

        # Act
        response = post_verify(client, "+79991234567", sender.last_code("+79991234567"))

        # Assert
        body = response.json()
        assert response.status_code == 200 and body["is_new"] is True
        assert body["token_type"] == "bearer" and body["access_token"].startswith("lk_")

    def test_logging_in_again_is_not_new_and_keeps_the_user(self, client, sender, clock):
        # Arrange
        post_code(client)
        first = post_verify(client, "+79991234567", sender.last_code("+79991234567")).json()
        clock.advance(minutes=2)
        post_code(client)

        # Act
        second = post_verify(client, "+79991234567", sender.last_code("+79991234567")).json()

        # Assert
        assert second["is_new"] is False and second["user_id"] == first["user_id"]

    def test_the_token_opens_the_profile(self, client, sender):
        # Arrange
        headers = login(client, sender, "+79991234567")

        # Act
        response = client.get("/me", headers=headers)

        # Assert
        assert response.status_code == 200 and response.json()["phone"] == "+79991234567"

    def test_a_wrong_code_gets_400(self, client, sender):
        # Arrange
        post_code(client)
        real = sender.last_code("+79991234567")

        # Act
        response = post_verify(client, "+79991234567", "000000" if real != "000000" else "111111")

        # Assert
        assert response.status_code == 400 and response.json()["detail"] == "Неверный код"

    def test_a_code_cannot_be_reused(self, client, sender):
        # Arrange
        post_code(client)
        code = sender.last_code("+79991234567")
        post_verify(client, "+79991234567", code)

        # Act
        response = post_verify(client, "+79991234567", code)

        # Assert
        assert response.status_code == 400

    def test_an_expired_code_gets_400(self, client, sender, clock):
        # Arrange
        post_code(client)
        code = sender.last_code("+79991234567")
        clock.advance(minutes=6)

        # Act
        response = post_verify(client, "+79991234567", code)

        # Assert
        assert response.status_code == 400 and "истёк" in response.json()["detail"]

    @pytest.mark.parametrize("code", ["12345", "1234567", "12ab56", "", "      "])
    def test_a_malformed_code_gets_422(self, client, code):
        # Arrange: фикстуры (client) и параметры теста (code)
        # Act
        response = post_verify(client, "+79991234567", code)

        # Assert
        assert response.status_code == 422

    def test_five_wrong_attempts_block_even_the_right_code(self, client, sender):
        # Arrange
        post_code(client)
        real = sender.last_code("+79991234567")
        wrong = "000000" if real != "000000" else "111111"
        for _ in range(5):
            post_verify(client, "+79991234567", wrong)

        # Act
        response = post_verify(client, "+79991234567", real)

        # Assert
        assert response.status_code == 400 and "попыток" in response.json()["detail"]


class TestAuthentication:
    @pytest.mark.parametrize("path", ["/me", "/feed", "/looks", "/favorites", "/wardrobe/items", "/weather"])
    def test_protected_routes_need_a_token(self, client, path):
        # Arrange: фикстуры (client) и параметры теста (path)
        # Act
        response = client.get(path)

        # Assert
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"

    @pytest.mark.parametrize("header", ["Bearer garbage", "Bearer ", "Basic abc", "lk_token-without-scheme"])
    def test_a_bad_authorization_header_is_refused(self, client, header):
        # Arrange: фикстуры (client) и параметры теста (header)
        # Act
        response = client.get("/me", headers={"Authorization": header})

        # Assert
        assert response.status_code == 401

    def test_an_expired_session_is_refused(self, client, user, clock):
        # Arrange
        clock.advance(days=91)

        # Act
        response = client.get("/me", headers=user)

        # Assert
        assert response.status_code == 401

    def test_public_routes_need_no_token(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        health, meta, products = client.get("/health"), client.get("/meta"), client.get("/products")

        # Assert
        assert (health.status_code, meta.status_code, products.status_code) == (200, 200, 200)


class TestLogout:
    def test_the_token_stops_working(self, client, user):
        # Arrange: состояние задают фикстуры (client, user)
        # Act
        response = client.post("/auth/logout", headers=user)

        # Assert
        assert response.status_code == 204
        assert client.get("/me", headers=user).status_code == 401

    def test_logging_out_needs_a_token(self, client):
        # Arrange: состояние задают фикстуры (client)
        # Act
        response = client.post("/auth/logout")

        # Assert
        assert response.status_code == 401

    def test_other_devices_stay_logged_in(self, client, sender, clock):
        # Arrange
        phone_a = login(client, sender, "+79990000001")
        phone_b = login(client, sender, "+79990000002")

        # Act
        client.post("/auth/logout", headers=phone_a)

        # Assert
        assert client.get("/me", headers=phone_b).status_code == 200
