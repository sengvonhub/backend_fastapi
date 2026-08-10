from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.users.user import User
from app.models.roles.role import Role
from app.models.departments.department import Department
from app.models.company import Company
from app.models.permission.permission import Permission
from app.core.security import hash_password
from app.core.permission import Permissions

ALL_PERMISSIONS = [
    Permissions.READ_OWN_PROFILE,
    Permissions.VIEW_USERS,
    Permissions.VIEW_OWN_ATTENDANCE,
    Permissions.VIEW_TEAM_ATTENDANCE,
    Permissions.MANAGE_ATTENDANCE_SETTINGS,
    Permissions.REQUEST_LEAVE,
    Permissions.APPROVE_LEAVE,
    Permissions.VIEW_TEAM_LEAVE,
    Permissions.VIEW_OWN_SALARY,
    Permissions.VIEW_TEAM_SALARY,
    Permissions.MANAGE_SALARY,
    Permissions.MANAGE_STAFF,
    Permissions.MANAGE_USERS,
    Permissions.VIEW_COMPANY,
    Permissions.MANAGE_COMPANY,
    Permissions.MANAGE_ROLES, 
    Permissions.MANAGE_DEPARTMENTS,
]

DEFAULT_ROLE_PERMISSIONS = {
    "admin": ALL_PERMISSIONS,
    "manager": [
        Permissions.READ_OWN_PROFILE,
        Permissions.VIEW_USERS,
        Permissions.VIEW_OWN_ATTENDANCE,
        Permissions.VIEW_TEAM_ATTENDANCE,
        Permissions.REQUEST_LEAVE,
        Permissions.APPROVE_LEAVE,
        Permissions.VIEW_TEAM_LEAVE,
        Permissions.VIEW_OWN_SALARY,
        Permissions.VIEW_TEAM_SALARY,
        Permissions.VIEW_COMPANY,
        Permissions.MANAGE_STAFF,
        Permissions.MANAGE_ROLES,
        Permissions.MANAGE_DEPARTMENTS,
    ],
    "staff": [
        Permissions.READ_OWN_PROFILE,
        Permissions.VIEW_OWN_ATTENDANCE,
        Permissions.REQUEST_LEAVE,
        Permissions.VIEW_OWN_SALARY,
        Permissions.VIEW_COMPANY,
    ],

}


async def seed_permissions(db: AsyncSession) -> None:
    """Idempotent — insert any Permissions.* not already in the DB."""
    result = await db.execute(select(Permission))
    existing = {p.code for p in result.scalars().all()}
    missing = [code for code in ALL_PERMISSIONS if code not in existing]
    if missing:
        db.add_all(Permission(code=c) for c in missing)
        await db.commit()
        print(f"✅ Synced {len(missing)} new permission(s): {missing}")


async def seed_data(db: AsyncSession):
    # 1. Permission catalog — must exist before roles reference it
    await seed_permissions(db)

    # 2. Company
    result = await db.execute(select(Company).where(Company.company_code == "DEFAULT"))
    company = result.scalar_one_or_none()
    if not company:
        company = Company(
            company_name="Default Company",
            company_code="DEFAULT",
            plan_type="enterprise",
            status="active",
        )
        db.add(company)
        await db.commit()
        await db.refresh(company)
        print("✅ Company created")
    else:
        print("⏭ Company already exists")

    # 3. Roles — WITH permissions attached
    all_perms_result = await db.execute(select(Permission))
    all_perms = {p.code: p for p in all_perms_result.scalars().all()}

    role_names = ["superuser", "admin", "manager", "staff"]
    for role_name in role_names:
        result = await db.execute(
            select(Role).where(Role.role_name == role_name, Role.company_id == company.company_id)
        )
        existing_role = result.scalar_one_or_none()

        if not existing_role:
            new_role = Role(company_id=company.company_id, role_name=role_name)
            perm_codes = DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
            new_role.permissions = [all_perms[c] for c in perm_codes if c in all_perms]
            db.add(new_role)

    await db.commit()
    print("✅ Roles seeded with permissions")

    # 4. Department
    result = await db.execute(
        select(Department).where(Department.department_name == "IT", Department.company_id == company.company_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        dept = Department(company_id=company.company_id, department_name="IT")
        db.add(dept)
        await db.commit()
        await db.refresh(dept)
        print("✅ Department created")

    # 5. Superuser account
    result = await db.execute(select(User).where(User.username == "admin"))
    admin = result.scalar_one_or_none()
    if not admin:
        result = await db.execute(
            select(Role).where(Role.role_name == "superuser", Role.company_id == company.company_id)
        )
        superuser_role = result.scalar_one()

        admin_user = User(
            company_id=company.company_id,
            username="admin",
            password_hash=hash_password("admin123"),
            full_name="System Admin",
            department_id=dept.department_id,
            role_id=superuser_role.role_id,
            status="active",
        )
        db.add(admin_user)
        await db.commit()
        print("✅ Superuser created: username=admin / password=admin123")
    else:
        print("⏭ Superuser already exists")