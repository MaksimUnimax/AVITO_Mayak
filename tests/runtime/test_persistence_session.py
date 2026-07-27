from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine

from mayak.persistence.session import create_session_factory, session_scope


def test_factory_settings() -> None:
    factory = create_session_factory(create_engine("postgresql+psycopg://u:p@localhost/mayak"))
    assert factory.kw["autoflush"] is False
    assert factory.kw["expire_on_commit"] is False


def test_success_commits_and_closes() -> None:
    session = Mock()
    factory = Mock(return_value=session)
    with session_scope(factory) as current:
        assert current is session
    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()
    session.close.assert_called_once_with()


def test_exception_rolls_back_closes_and_reraises() -> None:
    session = Mock()
    factory = Mock(return_value=session)
    failure = RuntimeError("synthetic failure")
    with pytest.raises(RuntimeError) as caught:
        with session_scope(factory):
            raise failure
    assert caught.value is failure
    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()
    session.close.assert_called_once_with()
