import os
from app.utils.logger import DefaultLogger
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from typing import List
from app.utils.services import search_articles
from app.models import VerificationResult, EvidenceItem
import re

logger = DefaultLogger("VerificationService").get_logger()

OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:4b')
OLLAMA_CONNECTION_STRING = os.getenv('OLLAMA_CONNECTION_STRING', 'http://ollama:11434')

class ClaimVerifier:
    _instance: "ClaimVerifier" = None

    def __init__(self):
        ollama_model = OpenAIModel(
            model_name=OLLAMA_MODEL, provider=OpenAIProvider(base_url=OLLAMA_CONNECTION_STRING + "/v1")
        )
        self.agent = Agent(
            ollama_model,
            result_type=VerificationResult,
            instrument=True,
            system_prompt=(
                "You evaluate whether a claim is true or false based on provided news contexts. "
                "Respond with JSON matching VerificationResult."
            ),
        )

        self.prompt_template = """
            Claim: {claim}\n
            Context: {context}\n
            Based on the above, is the claim True, False, or Undetermined?
            List up to three supporting evidence passages and reference them if you find them related to the claim."
        """

    @classmethod
    async def init_verifier(cls) -> "ClaimVerifier":
        if cls._instance is None:
            cls._instance = ClaimVerifier()
            logger.info("ClaimVerifier initialized successfully")
        return cls._instance

    @classmethod
    def get_verifier(cls) -> "ClaimVerifier":
        if cls._instance is None:
            raise Exception("ClaimVerifier not initialized; call init_verifier first")
        return cls._instance

    async def verify(self, claim: str) -> VerificationResult:
        """
        Embeds the claim, retrieves supporting context,
        and returns the final VerificationResult.
        """
        # ESTO ES PLACEHOLDER
        articles = await search_articles(claim)
        snippets = []
        for idx, art in enumerate(articles, 1):
            snippets.append(
                f"Article {idx}:\n"
                f"  Title: {art['Title']}\n"
                f"  Date:  {art['Date']}\n"
                f"  Summary: {art['Summary']}\n"
                f"  Source: {art['Source']}"
            )
        context = "\n\n".join(snippets)

        result = await self.agent.run(self.prompt_template.format(claim=claim, context=context))
        verification: VerificationResult = result.output

        # REFORMATEAR EVIDENCIAS
        structured: List[EvidenceItem] = []
        for ev in verification.Evidence:
            # SI YA TIENE ESTRUCTURA...
            if isinstance(ev, EvidenceItem):
                structured.append(ev)
            elif isinstance(ev, dict):
                structured.append(EvidenceItem(**ev))
            elif isinstance(ev, str):
                m = re.match(r"Article\s+(\d+):", ev)
                if m:
                    idx = int(m.group(1)) - 1
                    art = articles[idx]
                    structured.append(
                        EvidenceItem(
                            Title=art["Title"],
                            Source=art["Source"],
                            Date=art["Date"]
                        )
                    )
                else:
                    continue
            else:
                continue

        verification.Evidence = structured
        logger.info(f"Claim verification result: {verification.Verdict}")
        return verification