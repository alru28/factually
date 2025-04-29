from transformers import pipeline, AutoTokenizer
from collections import Counter
from app.utils.services import retrieve_article_content
from app.utils.logger import DefaultLogger
import torch


logger = DefaultLogger("TransformationService").get_logger()

class NLPProcessor:
    """
    A processor for performing various NLP tasks such as summarization, sentiment analysis,
    and zero-shot classification on articles retrieved from the storage service.
    
    This class handles long texts by chunking them to fit the model's maximum context length,
    processes each chunk individually, and then aggregates the results.
    """

    def __init__(self):
        """
        Initializes the NLPProcessor with pipelines and tokenizers for each task.
        Uses task-specific models for summarization, sentiment analysis, and classification.
        """

        device = 0 if torch.cuda.is_available() else -1

        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=device)
        self.sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", device=device)
        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=device)
        self.summarizer_tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
        self.sentiment_tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
        self.classify_tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-mnli")
        logger.info("NLPProcessor initialized with models and tokenizers.")
    
    async def summarize(self, article_id: str) -> str:
        """
        Summarizes the content of an article.
        
        The method retrieves the article content, splits it into manageable chunks based on the
        summarization model's context limit, generates partial summaries for each chunk, and then
        combines and optionally refines these partial summaries into a final summary.
        
        Args:
            article_id (str): The unique identifier for the article to summarize.
            
        Returns:
            str: A summary of the article.
        
        Raises:
            Exception: If the article has no content.
        """
        content = await retrieve_article_content(article_id)

        if not content:
            raise Exception(f"Article {article_id} has no content to summarize.")

        chunks = self.chunk_text(text=content, task="summarization")

        partial_summaries = [
            self.summarizer(chunk, max_length=300, min_length=50, do_sample=False)[0]["summary_text"]
            for chunk in chunks
        ]

        combined_summary = " ".join(partial_summaries)
        
        if len(self.summarizer_tokenizer.tokenize(combined_summary)) > 1024:
            final_summary = self.summarizer(combined_summary, max_length=400, min_length=100, do_sample=False)[0]["summary_text"]
        else:
            final_summary = combined_summary

        return final_summary
    
    def chunk_text(self, text: str, task: str) -> list:
        """
        Splits the input text into chunks that do not exceed the model's maximum token limit for a given task.
        
        The function uses different tokenizers and token limits based on the task:
          - "summarization": Uses summarizer_tokenizer with a max of 1024 tokens.
          - "sentiment": Uses sentiment_tokenizer with a max of 512 tokens.
          - "classification": Uses classify_tokenizer with a max of 1024 tokens.
        
        Args:
            text (str): The text to be chunked.
            task (str): The task for which the text is being processed. Must be one of "summarization",
                        "sentiment", or "classification".
            
        Returns:
            list: A list of text chunks, each within the specified token limit.
        """
        sentences = text.split(". ")
        chunks, current_chunk = [], ""

        if task == "summarization":
            tokenizer = self.summarizer_tokenizer
            max_tokens=1024
        elif task == "sentiment":
            tokenizer = self.sentiment_tokenizer
            max_tokens=512
        elif task == "classification":
            tokenizer = self.classify_tokenizer
            max_tokens=1024
        else:
            raise ValueError("Unsupported task specified. Use 'summarization', 'sentiment', or 'classification'.")

        for sentence in sentences:
            potential_chunk = current_chunk + sentence + ". "
            token_len = len(tokenizer.tokenize(potential_chunk))

            if token_len > max_tokens:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
            else:
                current_chunk = potential_chunk

        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks
    
    async def analyze_sentiment(self, article_id: str) -> dict:
        """
        Performs sentiment analysis on an article.
        
        The method retrieves the article content, splits it into chunks to respect the sentiment model's
        context length, performs sentiment analysis on each chunk, and aggregates the results using a
        majority vote for the label and an average of the confidence scores.
        
        Args:
            article_id (str): The unique identifier for the article to analyze.
            
        Returns:
            dict: A dictionary with keys "label" and "score", representing the overall sentiment.
        
        Raises:
            Exception: If the article has no content.
        """
        content = await retrieve_article_content(article_id)
        if not content:
            raise Exception(f"Article {article_id} has no content for sentiment analysis.")
        
        chunks = self.chunk_text(text=content, task="sentiment")
        sentiments = [self.sentiment_analyzer(chunk)[0] for chunk in chunks]
        
        labels = [result["label"] for result in sentiments]
        avg_score = sum(result["score"] for result in sentiments) / len(sentiments)
        
        majority_label = Counter(labels).most_common(1)[0][0]
        return {"label": majority_label, "score": avg_score}
    
    async def classify(self, article_id: str, candidate_labels: list = None) -> dict:
        """
        Classifies an article into one of the candidate labels using zero-shot classification.
        
        The method retrieves the article content, splits it into chunks to respect the classifier's
        context length, performs classification on each chunk, aggregates the scores for each candidate
        label across all chunks, and then normalizes the scores to determine the final classification.
        
        Args:
            article_id (str): The unique identifier for the article to classify.
            candidate_labels (list, optional): A list of candidate labels for classification.
                Defaults to ["economics", "sports", "entertainment", "politics", "technology", "culture", ""].
                
        Returns:
            dict: A dictionary containing the final label under the key "label" and the normalized scores
                  for each candidate label under the key "scores".
            
        Raises:
            Exception: If the article has no content.
        """
        if candidate_labels is None:
            candidate_labels = ["economics", "sports", "entertainment", "politics", "technology", "culture", "artificial intelligence"]
    
        content = await retrieve_article_content(article_id)
        if not content:
            raise Exception(f"Article {article_id} has no content to classify.")
        
        chunks = self.chunk_text(content, task="classification")
        
        aggregated_scores = {label: 0 for label in candidate_labels}
        for chunk in chunks:
            result = self.classifier(chunk, candidate_labels, truncate=True)
            for label, score in zip(result["labels"], result["scores"]):
                aggregated_scores[label] += score
        
        total = sum(aggregated_scores.values())
        normalized_scores = {label: score / total for label, score in aggregated_scores.items()}
        final_label = max(normalized_scores, key=normalized_scores.get)
        return {"label": final_label, "scores": normalized_scores}
    
_nlp_instance: NLPProcessor = None

def get_nlp_processor() -> NLPProcessor:
    global _nlp_instance
    if _nlp_instance is None:
        _nlp_instance = NLPProcessor()
        logger.info("Initialized NLPProcessor singleton instance.")
    return _nlp_instance