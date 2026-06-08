from pydantic import BaseModel, Field
from typing import List, Optional


class ArticleSection(BaseModel):
    heading: str = Field(description="The subtitle or trend title.")
    body: str = Field(description="The paragraphs explaining this specific trend.")
    cognitive_load: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Working memory demand of this section (0.0 = very accessible, 1.0 = highly demanding).",
    )
    emotional_valence: Optional[str] = Field(
        default=None,
        description="Emotional register of this section. Must be exactly one of: uplifting, neutral, cautionary, reflective, mixed.",
    )
    review_prompts: Optional[List[str]] = Field(
        default=None,
        description="2 to 3 spaced-repetition recall questions testing distinct key concepts from the section.",
    )


class StructuredBlogPost(BaseModel):
    title: str = Field(description="An attention-grabbing title for the article.")
    author: str = Field(description="The author of the article.")
    sections: List[ArticleSection] = Field(description="The structured breakdowns of the article.")
    generated_at: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp of when this post was generated. Injected by reports.py, not the LLM.",
    )
