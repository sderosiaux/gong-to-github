"""Data models for Gong API responses."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class Affiliation(str, Enum):
    INTERNAL = "Internal"
    EXTERNAL = "External"
    UNKNOWN = "Unknown"


class Participant(BaseModel):
    """A participant in a Gong call."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    email_address: str | None = Field(default=None, alias="emailAddress")
    name: str | None = None
    title: str | None = None
    speaker_id: str | None = Field(default=None, alias="speakerId")
    affiliation: Affiliation | None = None
    user_id: str | None = Field(default=None, alias="userId")


class CallMetadata(BaseModel):
    """Metadata for a Gong call."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    url: str | None = None
    title: str | None = None
    scheduled: datetime | None = None
    started: datetime | None = None
    duration: int | None = None  # in seconds
    direction: str | None = None
    system: str | None = None
    scope: str | None = None
    media: str | None = None
    language: str | None = None
    primary_user_id: str | None = Field(default=None, alias="primaryUserId")


class Sentence(BaseModel):
    """A sentence in a transcript."""

    model_config = ConfigDict(populate_by_name=True)

    start_ms: int = Field(validation_alias=AliasChoices("startMs", "start"))
    end_ms: int = Field(validation_alias=AliasChoices("endMs", "end"))
    text: str


class TranscriptSegment(BaseModel):
    """A segment of transcript from one speaker."""

    model_config = ConfigDict(populate_by_name=True)

    speaker_id: str = Field(alias="speakerId")
    sentences: list[Sentence]


class CallTranscript(BaseModel):
    """Transcript for a call."""

    model_config = ConfigDict(populate_by_name=True)

    call_id: str = Field(alias="callId")
    transcript: list[TranscriptSegment]


class Call(BaseModel):
    """A complete call with metadata, participants, and transcript."""

    model_config = ConfigDict(populate_by_name=True)

    metadata: CallMetadata = Field(alias="metaData")
    parties: list[Participant] = Field(default_factory=list)
    transcript: list[TranscriptSegment] = Field(default_factory=list)
    context: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def client_name(self) -> str | None:
        """Extract the client/account name from external participants or context."""
        # Try to get from Salesforce context
        for ctx in self.context:
            if ctx.get("system") == "Salesforce":
                for obj in ctx.get("objects", []):
                    if obj.get("objectType") == "Account":
                        for field in obj.get("fields", []):
                            if field.get("name") == "Name":
                                return field.get("value")

        # Fallback: get company from first external participant's email domain
        for party in self.parties:
            if party.affiliation == Affiliation.EXTERNAL and party.email_address:
                domain = party.email_address.split("@")[-1]
                # Remove common suffixes
                company = domain.split(".")[0]
                return company.title()

        return None

    @property
    def external_participants(self) -> list[Participant]:
        """Get all external participants."""
        return [p for p in self.parties if p.affiliation == Affiliation.EXTERNAL]

    @property
    def internal_participants(self) -> list[Participant]:
        """Get all internal participants."""
        return [p for p in self.parties if p.affiliation == Affiliation.INTERNAL]


class User(BaseModel):
    """A Gong user."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    email_address: str = Field(alias="emailAddress")
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    active: bool = True

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or self.email_address


