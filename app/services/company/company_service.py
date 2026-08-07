from fastapi import HTTPException, status, UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import asyncio

from app.repositories.company.company_repository import CompanyRepository
from app.repositories.auth.refresh_token_repository import RefreshTokenRepo
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    UpdatePlanRequest,
    UpdateStatusRequest,
    CompanyRegisterRequest,
)
from app.services.storage import CloudinaryStorage
from app.models.roles.role import Role
from app.models.permission.permission import Permission
from app.models.users.user import User, UserStatus
from app.core.security import hash_password, create_access_token, create_refresh_token
from app.core.permission import Permissions
from app.core.config import settings

storage = CloudinaryStorage()

ALL_PERMISSIONS = [
    Permissions.READ_OWN_PROFILE, Permissions.VIEW_USERS,
    Permissions.VIEW_OWN_ATTENDANCE, Permissions.VIEW_TEAM_ATTENDANCE,
    Permissions.MANAGE_ATTENDANCE_SETTINGS, Permissions.REQUEST_LEAVE,
    Permissions.APPROVE_LEAVE, Permissions.VIEW_TEAM_LEAVE,
    Permissions.VIEW_OWN_SALARY, Permissions.VIEW_TEAM_SALARY,
    Permissions.MANAGE_SALARY, Permissions.MANAGE_STAFF,
    Permissions.MANAGE_USERS, Permissions.VIEW_COMPANY, Permissions.MANAGE_COMPANY,
]

DEFAULT_ROLE_PERMISSIONS = {
    "superuser": ALL_PERMISSIONS,
    "admin":     ALL_PERMISSIONS,
    "manager": [
        Permissions.READ_OWN_PROFILE, Permissions.VIEW_USERS,
        Permissions.VIEW_OWN_ATTENDANCE, Permissions.VIEW_TEAM_ATTENDANCE,
        Permissions.REQUEST_LEAVE, Permissions.APPROVE_LEAVE,
        Permissions.VIEW_TEAM_LEAVE, Permissions.VIEW_OWN_SALARY,
        Permissions.VIEW_TEAM_SALARY, Permissions.VIEW_COMPANY,
    ],
    "staff": [
        Permissions.READ_OWN_PROFILE, Permissions.VIEW_OWN_ATTENDANCE,
        Permissions.REQUEST_LEAVE, Permissions.VIEW_OWN_SALARY, Permissions.VIEW_COMPANY,
    ],
}




class CompanyService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CompanyRepository(db)
        self.refresh_repo = RefreshTokenRepo(db)

    # -----------------------------------------------------------------------
    # GET all companies
    # -----------------------------------------------------------------------

    async def get_all(self) -> list:
        return await self.repo.get_all()

    # -----------------------------------------------------------------------
    # GET one company
    # -----------------------------------------------------------------------

    async def get_by_id(self, company_id: int):
        company = await self.repo.get_by_id(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company id={company_id} not found.",
            )
        return company

    # -----------------------------------------------------------------------
    # CREATE company (admin-only — existing internal flow, unchanged)
    # -----------------------------------------------------------------------

    async def create(self, data: CompanyCreate):
        existing = await self.repo.get_by_code(data.company_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Company code '{data.company_code}' already exists.",
            )
        return await self.repo.create({
            "company_name": data.company_name,
            "company_code": data.company_code.upper(),
            "email":        data.email,
            "phone":        data.phone,
            "address":      data.address,
            "logo_url":     data.logo_url,
            "plan_type":    data.plan_type,
            "status":       "active",
            "timezone":     data.timezone,
            "currency":     data.currency,
            "max_users":    data.max_users,
        })

    # -----------------------------------------------------------------------
    # REGISTER — public, unauthenticated: new company + owner account
    # -----------------------------------------------------------------------

    async def register(self, body: CompanyRegisterRequest, client_ip: str) -> dict:
        # =============================================
        #   COMPANY + OWNER REGISTRATION LOGIC
        # =============================================
        if await self.repo.get_by_code(body.company_code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Company code '{body.company_code}' already exists.",
            )

        # =============================================
        #  OWNER USERNAME CHECK
        # =============================================

        existing_user = await self.db.execute(
            select(User).where(User.username == body.admin_username)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken.",
            )
        
        # ============================================
        # 3. create company
        # ============================================
 
        company = await self.repo.create({
            "company_name": body.company_name,
            "company_code": body.company_code.upper(),
            "email":        body.email,
            "phone":        body.phone,
            "address":      body.address,
            "plan_type":    body.plan_type,
            "status":       "active",
            "timezone":     body.timezone,
            "currency":     body.currency,
            "max_users":    body.max_users,
        })  


        # =======================================================
        # 4. ensure global permission catalog exists (idempotent)
        # =======================================================


        existing_perms = await self.db.execute(select(Permission))
        perm_map = {p.code: p for p in existing_perms.scalars().all()}
        missing = [c for c in ALL_PERMISSIONS if c not in perm_map]
        if missing:
            new_perms = [Permission(code=c) for c in missing]
            self.db.add_all(new_perms)
            await self.db.commit()
            for p in new_perms:
                await self.db.refresh(p)
                perm_map[p.code] = p


        # =====================================================================
        # 5. seed roles scoped to THIS company, with real permissions attached
        # =====================================================================

        roles_by_name = {}
        for role_name, perm_codes in DEFAULT_ROLE_PERMISSIONS.items():
            role = Role(company_id=company.company_id, role_name=role_name)
            role.permissions = [perm_map[c] for c in perm_codes if c in perm_map]
            self.db.add(role)
            roles_by_name[role_name] = role
        await self.db.commit()
        for r in roles_by_name.values():
            await self.db.refresh(r)

        # =====================================================================
        # 6. create the owner user as this company's superuser
        # =====================================================================

        superuser_role = roles_by_name["superuser"]
        user = User(
            company_id=company.company_id,
            username=body.admin_username,
            password_hash=hash_password(body.admin_password),
            full_name=body.admin_full_name,
            role_id=superuser_role.role_id,
            status=UserStatus.active,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)






        # =====================================================================
        # 7. issue tokens immediately — no separate login step needed
        # =====================================================================

        access_token = create_access_token({
            "sub":         str(user.user_id),
            "company_id":  company.company_id,
            "role":        "superuser",
            "permissions": ["*"],
            "staff_id":    None,
            "is_manager":  False,
        })
        refresh_token = create_refresh_token(user.user_id, company.company_id)
        await self.refresh_repo.save(
            user_id=user.user_id,
            company_id=company.company_id,
            token=refresh_token,
        )
        return {
            "access_token":       access_token,
            "refresh_token":      refresh_token,
            "access_expires_in":  settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            "token_type":         "bearer",
            "company": {
                "company_id":   company.company_id,
                "company_name": company.company_name,
                "company_code": company.company_code,
                "plan_type":    company.plan_type,
                "status":       company.status,
                "max_users":    company.max_users,
            },
            "user": {
                "user_id":   user.user_id,
                "username":  user.username,
                "full_name": user.full_name,
                "role":      "superuser",
            },
        }




    # -----------------------------------------------------------------------
    # UPDATE company info
    # -----------------------------------------------------------------------

    async def update(self, company_id: int, data: CompanyUpdate):
        company = await self.get_by_id(company_id)
        return await self.repo.update(company, data.model_dump(exclude_none=True))

    async def update_media(
        self,
        company_id:           int,
        logo:                 Optional[UploadFile] = None,
        banner:               Optional[UploadFile] = None,
        old_logo_public_id:   Optional[str]        = None,
        old_banner_public_id: Optional[str]        = None,
    ):
        company = await self.get_by_id(company_id)
        update_data = {}

        if logo and logo.filename:
            if old_logo_public_id:
                await storage.delete_asset(old_logo_public_id, resource_type="image")
            result = await storage.upload_image(logo, folder="companies/logos")
            update_data["logo_url"]       = result["secure_url"]
            update_data["logo_public_id"] = result["public_id"]

        if banner and banner.filename:
            if old_banner_public_id:
                await storage.delete_asset(old_banner_public_id, resource_type="image")
            result = await storage.upload_image(banner, folder="companies/banners")
            update_data["banner_url"]       = result["secure_url"]
            update_data["banner_public_id"] = result["public_id"]

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No media files provided.",
            )

        return await self.repo.update(company, update_data)

    # -----------------------------------------------------------------------
    # DELETE company
    # -----------------------------------------------------------------------

    async def delete(self, company_id: int, background_tasks: BackgroundTasks) -> dict:
        company = await self.get_by_id(company_id)

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        await self.repo.delete(company)

        if company.logo_public_id:
            background_tasks.add_task(storage.delete_asset, company.logo_public_id)

        if company.banner_public_id:
            background_tasks.add_task(storage.delete_asset, company.banner_public_id)

        return {
            "message": f"Company '{company.company_name}' deleted successfully"
        }

    # -----------------------------------------------------------------------
    # UPDATE plan (superuser only)
    # -----------------------------------------------------------------------

    async def update_plan(self, company_id: int, data: UpdatePlanRequest):
        company = await self.get_by_id(company_id)

        update_data = {"plan_type": data.plan_type}
        if data.max_users:
            update_data["max_users"] = data.max_users
        if data.expires_at:
            update_data["expires_at"] = data.expires_at

        return await self.repo.update(company, update_data)

    # -----------------------------------------------------------------------
    # UPDATE status (superuser only)
    # -----------------------------------------------------------------------

    async def update_status(self, company_id: int, data: UpdateStatusRequest, changed_by: int):
        company = await self.get_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        old_status = company.status
        company = await self.repo.update(company, {"status": data.status})

        history = await self.repo.log_status_history(
            company_id=company.company_id,
            old_status=old_status,
            new_status=data.status,
            reason=data.reason,
            changed_by=changed_by,
        )

        return history

    # -----------------------------------------------------------------------
    # GET settings
    # -----------------------------------------------------------------------

    async def get_settings(self, company_id: int):
        return await self.get_by_id(company_id)

    # -----------------------------------------------------------------------
    # GET stats
    # -----------------------------------------------------------------------

    async def get_stats(self, company_id: int) -> dict:
        company = await self.get_by_id(company_id)
        stats   = await self.repo.get_stats(company_id)
        return {
            "company_id":   company.company_id,
            "company_name": company.company_name,
            **stats,
        }