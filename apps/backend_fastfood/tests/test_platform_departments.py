"""Department persistence tests using an isolated in-memory database."""
import unittest
from contextlib import asynccontextmanager

from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models.platform_department import PlatformDepartment
from models.platform_employee import PlatformEmployee
from schemas.platform_employee import PlatformDepartmentCreate
from services.platform_hr_service import PlatformHRService


class AsyncSessionAdapter:
    def __init__(self, session):
        self.session = session

    async def execute(self, statement):
        return self.session.execute(statement)

    async def scalars(self, statement):
        return self.session.scalars(statement)

    async def scalar(self, statement):
        return self.session.scalar(statement)

    def add(self, row):
        self.session.add(row)

    async def flush(self):
        self.session.flush()

    async def commit(self):
        self.session.commit()

    @asynccontextmanager
    async def begin_nested(self):
        with self.session.begin_nested():
            yield


class DepartmentTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        PlatformEmployee.__table__.create(self.engine)
        PlatformDepartment.__table__.create(self.engine)
        self.session = Session(self.engine)
        self.service = PlatformHRService(AsyncSessionAdapter(self.session))

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    async def test_persists_without_employee_and_reuses_duplicate(self):
        self.assertEqual(await self.service.create_department('  Finance  '), 'Finance')
        self.assertEqual(await self.service.create_department('finance'), 'Finance')
        self.session.close()
        self.assertEqual(await self.service.departments(), ['Finance'])

    async def test_existing_employee_departments_remain_available(self):
        self.session.add(PlatformEmployee(employee_no='PLT-0001', seq=1, full_name='Sam', department='Sales'))
        self.session.commit()
        await self.service.create_department('Support')
        self.assertEqual(await self.service.departments(), ['Sales', 'Support'])
        self.assertEqual(await self.service.create_department('sales'), 'Sales')

    def test_department_name_validation(self):
        self.assertEqual(PlatformDepartmentCreate(name='  HR  ').name, 'HR')
        for name in ['', '   ', 'x' * 81]:
            with self.assertRaises(ValidationError):
                PlatformDepartmentCreate(name=name)
