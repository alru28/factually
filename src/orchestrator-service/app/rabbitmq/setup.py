def declare_exchange_queues(channel):
    # Declare a topic exchange
    channel.exchange_declare(exchange='Articles', exchange_type='topic', durable=True)
    
    # Declare queues for scraping and NLP processing
    channel.queue_declare(queue='Scraped', durable=True)
    channel.queue_declare(queue='Enriched', durable=True)
    
    # Bind queues to the exchange with routing keys
    channel.queue_bind(exchange='Articles', queue='Scraped', routing_key='articles.scraped')
    channel.queue_bind(exchange='Articles', queue='Enriched', routing_key='articles.nlp')
