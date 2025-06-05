import os
from app.utils.logger import DefaultLogger
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from typing import List
from app.utils.services import search_articles
from app.models import VerificationResult, EvidenceItem, WebEvidenceItem
import re

logger = DefaultLogger().get_logger()

OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:4b')
OLLAMA_CONNECTION_STRING = os.getenv('OLLAMA_CONNECTION_STRING', 'http://ollama:11434')

class ClaimVerifier:
    _instance: "ClaimVerifier" = None

    def __init__(self):
        ollama_model = OpenAIModel(
            model_name=OLLAMA_MODEL, provider=OpenAIProvider(base_url=OLLAMA_CONNECTION_STRING + "/v1")
        )
        self.verifier_agent = Agent(
            ollama_model,
            result_type=VerificationResult,
            instrument=True,
            system_prompt=(
                "You evaluate whether a claim is true or false based on provided news contexts. "
                "Respond with JSON matching VerificationResult."
            ),
        )

        self.search_agent = Agent(
            OpenAIModel(
                model_name=OLLAMA_MODEL, provider=OpenAIProvider(base_url=OLLAMA_CONNECTION_STRING + "/v1")
            ),
            tools=[duckduckgo_search_tool()],
            result_type=List[WebEvidenceItem],
            instrument=True,
            system_prompt=(
                "You are a fact-checking assistant. When provided with a claim, "
                "search the web using DuckDuckGo to find relevant information that can help verify the claim. "
                "Respond with JSON matching List[WebEvidenceItem]."
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

    async def verify(self, claim: str, web_search: bool) -> VerificationResult:
        """
        Embeds the claim, retrieves supporting context,
        and returns the final VerificationResult.
        """
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

        result = await self.verifier_agent.run(self.prompt_template.format(claim=claim, context=context))
        verification: VerificationResult = result.output   

        # REFORMAT EVIDENCE
        structured: List[EvidenceItem] = []
        for ev in verification.Evidence:
            if isinstance(ev, EvidenceItem):
                # IF STRUCTURED...
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

        if verification.Verdict.lower() == "undetermined" and web_search:
            try:
                logger.info("Verification result is undetermined, performing web search for additional evidence.")
                search_result = await self.search_agent.run(claim)
                additional_evidence: List[WebEvidenceItem] = search_result.output
                verification.Evidence = additional_evidence
                verification.WebSearchPerformed = True
                logger.info(f"Web search performed, found {len(additional_evidence)} additional web evidence items.")

                new_context = []
                for idx, entry in enumerate(additional_evidence, 1):
                    new_context.append(
                        f"Web Entry {idx}:\n"
                        f"  Title: {entry.Title}\n"
                        f"  Date:  {entry.Date}\n"
                        f"  Source: {entry.Source}\n"
                        f"  Summary: {entry.Summary}"
                    )
                
                web_verification_result = await self.verifier_agent.run(self.prompt_template.format(claim=claim, context=new_context))
                web_verification: VerificationResult = web_verification_result.output

                reassessed_structured: List[EvidenceItem] = []
                for ev in web_verification.Evidence:
                    if isinstance(ev, EvidenceItem):
                        reassessed_structured.append(ev)
                    elif isinstance(ev, dict):
                        reassessed_structured.append(EvidenceItem(**ev))
                    elif isinstance(ev, str):
                        m = re.match(r"Article\s+(\d+):", ev)
                        if m:
                            idx = int(m.group(1)) - 1
                            art = articles[idx]
                            reassessed_structured.append(
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
                web_verification.Evidence = reassessed_structured
                web_verification.WebSearchPerformed = True

                logger.info(f"Claim  reassessment using web search result: {web_verification.Verdict}")
                return web_verification
            
            except Exception as e:
                logger.error(f"Error during web search: {e}")
                verification.WebSearchPerformed = False

        logger.info(f"Claim verification result: {verification.Verdict}")
        return verification