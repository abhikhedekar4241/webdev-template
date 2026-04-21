import re
import uuid
from datetime import datetime, timedelta

import factory

from app.models.invitation import InvitationStatus, OrgInvitation
from app.models.org import Organization, OrgMembership, OrgRole


class OrgFactory(factory.Factory):
    class Meta:
        model = Organization

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker("company")
    slug = factory.LazyAttribute(
        lambda o: re.sub(r"[^a-z0-9-]", "-", o.name.lower())[:30]
    )
    created_by = factory.LazyFunction(uuid.uuid4)
    deleted_at = None
    created_at = factory.LazyFunction(datetime.utcnow)


class MembershipFactory(factory.Factory):
    class Meta:
        model = OrgMembership

    id = factory.LazyFunction(uuid.uuid4)
    org_id = factory.LazyFunction(uuid.uuid4)
    user_id = factory.LazyFunction(uuid.uuid4)
    role = OrgRole.member
    joined_at = factory.LazyFunction(datetime.utcnow)


class InvitationFactory(factory.Factory):
    class Meta:
        model = OrgInvitation

    id = factory.LazyFunction(uuid.uuid4)
    org_id = factory.LazyFunction(uuid.uuid4)
    invited_email = factory.Sequence(lambda n: f"invite{n}@example.com")
    role = OrgRole.member
    invited_by = factory.LazyFunction(uuid.uuid4)
    status = InvitationStatus.pending
    expires_at = factory.LazyFunction(lambda: datetime.utcnow() + timedelta(days=7))
    created_at = factory.LazyFunction(datetime.utcnow)
