"""Bounded linkedin operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import LinkedInClient


class Client(BaseClient):
    provider = "linkedin"
    implementation = LinkedInClient
    origins = ("https://linkedin-api8.p.rapidapi.com", "https://www.linkedin.com")
    operations = (
        "get_profile",
        "search_people",
        "get_profile_posts",
        "get_post_comments",
        "get_similar_profiles",
        "get_company_details",
        "search_companies",
        "get_company_jobs",
        "get_company_posts",
        "get_company_post_comments",
        "search_posts",
        "get_post",
        "get_job_details",
        "search_jobs",
        "search_locations",
    )
