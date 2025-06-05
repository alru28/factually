import json
from app.utils.logger import DefaultLogger
from app.main import get_rabbitmq_client
from app.nlp.processor import get_nlp_processor
from app.utils.services import store_processed_article


logger = DefaultLogger().get_logger()

nlp_processor = get_nlp_processor()

async def publish_message(message: dict, routing_key: str):
    try:
        client = await get_rabbitmq_client()
        await client.publish(message, routing_key)
    except Exception as e:
        logger.error(f"Failed to publish message to routing key '{routing_key}': {e}")

async def handle_message(message):
    payload = json.loads(message.body.decode('utf-8'))
    correlation_id = payload.get('correlation_id')

    if payload.get("status") == "transformation":
        article_ids = payload.get("article_ids")
        if not article_ids:
            logger.error("No article_ids provided in transformation task")
        else:
            results = []
            for article_id in article_ids:
                try:
                    summary = await nlp_processor.summarize(str(article_id))
                    classification = await nlp_processor.classify(str(article_id))
                    sentiment = await nlp_processor.analyze_sentiment(str(article_id))

                    enriched_content = {
                        "Summary": summary,
                        "Sentiment": sentiment["label"],
                        "Classification": [classification["label"]]
                    }

                    await store_processed_article(str(article_id), enriched_content)

                    results.append({"article_id": article_id, "summary": summary, "classification": classification, "sentiment": sentiment})
                    logger.debug(f"Article {article_id} processed successfully")
                except Exception as e:
                    logger.error(f"Error processing article {article_id}: {e}")

            new_payload = {
                "correlation_id": correlation_id,
                "status": "transformation_complete",
                "article_ids": article_ids,
                "article_count": len(results),
            }

            await publish_message(new_payload, routing_key="completion")
            logger.info(f"Published completion task for correlation_id {correlation_id}")
    else:
        logger.warning("Received message with unsupported status. No action taken.")

    await message.ack()