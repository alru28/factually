import os
from app.utils.logger import DefaultLogger
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from typing import List
from app.utils.services import search_articles

logger = DefaultLogger("VerificationService").get_logger()

OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'cogito:8b')

class VerificationResult(BaseModel):
    claim: str
    verdict: str  # 'true', 'false', or 'undetermined'
    evidence: List[str]

class Deps(BaseModel):
    retrieve_params: dict

class ClaimVerifier:
    _instance: "ClaimVerifier" = None

    def __init__(self, deps: Deps):
        ollama_model = OpenAIModel(
            model_name=OLLAMA_MODEL, provider=OpenAIProvider(base_url='http://localhost:11434/v1')
        )
        self.agent = Agent(
            ollama_model,
            deps_type=Deps,
            result_type=VerificationResult,
            instrument=True,
            system_prompt=(
                "You evaluate whether a claim is true or false based on provided news contexts. "
                "Respond with JSON matching VerificationResult."
            ),
        )

        # TOOLS
        @self.agent.tool
        async def retrieve(ctx: RunContext[Deps], query: str) -> str:
            articles = await search_articles(query, ctx.deps.retrieve_params)
            snippets = []
            for idx, art in enumerate(articles, 1):
                snippets.append(
                    f"Article {idx}:\n"
                    f"  Title: {art.Title}\n"
                    f"  Date:  {art.Date}\n"
                    f"  Summary: {art.Summary}\n"
                    f"  Source: {art.Source}"
                )
            return "\n\n".join(snippets)

        @self.agent.tool
        async def verify_claim(
            ctx: RunContext[Deps], claim: str, context: str
        ) -> VerificationResult:
            prompt = (
                f"Claim: {claim}\n\n"
                f"News Context:\n{context}\n\n"
                "Based on the above, is the claim True, False, or Undetermined? "
                "List up to three supporting evidence passages and reference them."
            )
            # ESTO ES PLACEHOLDER
            return await ctx.run_llm(prompt)

        self.deps = deps

    @classmethod
    async def init_verifier(cls, retrieve_params: dict) -> "ClaimVerifier":
        if cls._instance is None:
            deps = Deps(retrieve_params=retrieve_params)
            cls._instance = ClaimVerifier(deps)
            logger.info("ClaimVerifier initialized successfully")
        return cls._instance

    @classmethod
    def get_client(cls) -> "ClaimVerifier":
        if cls._instance is None:
            raise Exception("ClaimVerifier not initialized; call init_verifier first")
        return cls._instance

    async def verify(self, claim: str) -> VerificationResult:
        """
        Embeds the claim, retrieves supporting context,
        and returns the final VerificationResult.
        """
        # ESTO ES PLACEHOLDER
        context = await self.agent.invoke_tool("retrieve", search_query=claim, deps=self.deps)

        result: VerificationResult = await self.agent.invoke_tool(
            "verify_claim", claim=claim, context=context, deps=self.deps
        )
        logger.info(f"Claim verification result: {result.json()}")
        return result